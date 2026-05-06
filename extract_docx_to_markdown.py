from __future__ import annotations

import argparse
import posixpath
import re
import shutil
import zipfile
from collections import OrderedDict
from pathlib import Path

from lxml import etree


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
}


def clean_text(value: str) -> str:
    value = value.replace("\u00a0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def part_rels_name(part_name: str) -> str:
    folder, filename = posixpath.split(part_name)
    rels_file = f"{filename}.rels"
    return posixpath.join(folder, "_rels", rels_file) if folder else posixpath.join("_rels", rels_file)


def load_rels(zf: zipfile.ZipFile, part_name: str) -> dict[str, str]:
    rels_path = part_rels_name(part_name)
    if rels_path not in zf.namelist():
        return {}
    rels_root = etree.fromstring(zf.read(rels_path))
    base_dir = posixpath.dirname(part_name)
    rels: dict[str, str] = {}
    for rel in rels_root.xpath("./rel:Relationship", namespaces=NS):
        rid = rel.get("Id")
        target = rel.get("Target")
        if not rid or not target or target.startswith("http://") or target.startswith("https://"):
            continue
        resolved = posixpath.normpath(posixpath.join(base_dir, target))
        rels[rid] = resolved
    return rels


def paragraph_style(paragraph: etree._Element) -> str:
    style = paragraph.find("./w:pPr/w:pStyle", namespaces=NS)
    return style.get(f"{{{NS['w']}}}val", "") if style is not None else ""


def paragraph_text(paragraph: etree._Element) -> str:
    pieces: list[str] = []
    paragraph_is_inside_textbox = bool(paragraph.xpath("ancestor::w:txbxContent", namespaces=NS))
    for node in paragraph.iter():
        if not paragraph_is_inside_textbox and node.xpath("ancestor::w:txbxContent", namespaces=NS):
            continue
        tag = etree.QName(node).localname
        if tag == "t" and node.text:
            pieces.append(node.text)
        elif tag == "tab":
            pieces.append("\t")
        elif tag in {"br", "cr"}:
            pieces.append("\n")
    return clean_text("".join(pieces))


def cell_text(cell: etree._Element) -> str:
    lines: list[str] = []
    for p in cell.xpath(".//w:p", namespaces=NS):
        text = paragraph_text(p)
        if text:
            lines.append(text)
    text = "<br>".join(lines)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    return text.replace("|", "\\|")


def table_markdown(table: etree._Element) -> list[str]:
    rows: list[list[str]] = []
    for tr in table.xpath("./w:tr", namespaces=NS):
        row = [cell_text(tc) for tc in tr.xpath("./w:tc", namespaces=NS)]
        if any(cell.strip() for cell in row):
            rows.append(row)
    if not rows:
        return []
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    header = rows[0]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * width) + " |"]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def extract_images_from_node(
    zf: zipfile.ZipFile,
    node: etree._Element,
    rels: dict[str, str],
    images_dir: Path,
    image_records: OrderedDict[str, str],
) -> list[str]:
    links: list[str] = []
    ids = []
    ids.extend(node.xpath(".//a:blip/@r:embed", namespaces=NS))
    ids.extend(node.xpath(".//v:imagedata/@r:id", namespaces=NS))
    for rid in ids:
        target = rels.get(rid)
        if not target or target not in zf.namelist():
            continue
        if target not in image_records:
            suffix = Path(target).suffix or ".bin"
            filename = f"image-{len(image_records) + 1:03d}{suffix}"
            out_path = images_dir / filename
            out_path.write_bytes(zf.read(target))
            image_records[target] = filename
        links.append(f"![{Path(target).name}](images/{image_records[target]})")
    return links


def paragraph_markdown(
    zf: zipfile.ZipFile,
    paragraph: etree._Element,
    rels: dict[str, str],
    images_dir: Path,
    image_records: OrderedDict[str, str],
) -> list[str]:
    lines: list[str] = []
    text = paragraph_text(paragraph)
    style = paragraph_style(paragraph).lower()
    if text:
        if style.startswith("heading1") or style in {"title", "titlestyle"}:
            lines.append(f"# {text}")
        elif style.startswith("heading2"):
            lines.append(f"## {text}")
        elif style.startswith("heading3"):
            lines.append(f"### {text}")
        elif "heading" in style:
            lines.append(f"#### {text}")
        else:
            lines.append(text)
    for textbox in paragraph.xpath(".//w:txbxContent", namespaces=NS):
        for textbox_paragraph in textbox.xpath("./w:p", namespaces=NS):
            textbox_text = paragraph_text(textbox_paragraph)
            if textbox_text:
                lines.append(textbox_text)
    lines.extend(extract_images_from_node(zf, paragraph, rels, images_dir, image_records))
    return lines


def part_markdown(
    zf: zipfile.ZipFile,
    part_name: str,
    images_dir: Path,
    image_records: OrderedDict[str, str],
) -> list[str]:
    if part_name not in zf.namelist():
        return []
    root = etree.fromstring(zf.read(part_name))
    rels = load_rels(zf, part_name)
    body = root.find(".//w:body", namespaces=NS)
    children = list(body) if body is not None else root.xpath(".//w:p | .//w:tbl", namespaces=NS)
    lines: list[str] = []
    for child in children:
        local = etree.QName(child).localname
        if local == "p":
            block = paragraph_markdown(zf, child, rels, images_dir, image_records)
            if block:
                lines.extend(block)
                lines.append("")
        elif local == "tbl":
            tbl_lines = table_markdown(child)
            if tbl_lines:
                lines.extend(tbl_lines)
                lines.append("")
            image_links = extract_images_from_node(zf, child, rels, images_dir, image_records)
            if image_links:
                lines.extend(image_links)
                lines.append("")
    return lines


def unique_nonempty_blocks(parts: list[list[str]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for lines in parts:
        text = clean_text("\n".join(lines))
        if not text or text in seen:
            continue
        seen.add(text)
        out.extend(lines)
        if out and out[-1] != "":
            out.append("")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args()

    out_dir = args.out_dir
    images_dir = out_dir / "images"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    images_dir.mkdir(parents=True, exist_ok=True)

    image_records: OrderedDict[str, str] = OrderedDict()
    with zipfile.ZipFile(args.docx) as zf:
        md_lines = [f"# {args.docx.stem}", ""]
        md_lines.extend(part_markdown(zf, "word/document.xml", images_dir, image_records))

        header_footer_parts = [
            name
            for name in zf.namelist()
            if re.match(r"word/(header|footer)\d+\.xml$", name)
        ]
        hf_blocks = [part_markdown(zf, name, images_dir, image_records) for name in sorted(header_footer_parts)]
        hf_lines = unique_nonempty_blocks(hf_blocks)
        if hf_lines:
            md_lines.extend(["## Headers and Footers", ""])
            md_lines.extend(hf_lines)

        for extra_title, pattern in [
            ("Footnotes", r"word/footnotes\.xml$"),
            ("Endnotes", r"word/endnotes\.xml$"),
            ("Comments", r"word/comments\.xml$"),
        ]:
            names = [name for name in zf.namelist() if re.match(pattern, name)]
            blocks = [part_markdown(zf, name, images_dir, image_records) for name in names]
            extra_lines = unique_nonempty_blocks(blocks)
            if extra_lines:
                md_lines.extend([f"## {extra_title}", ""])
                md_lines.extend(extra_lines)

        media_names = [name for name in zf.namelist() if name.startswith("word/media/")]
        unreferenced = [name for name in media_names if name not in image_records]
        if unreferenced:
            md_lines.extend(["## Additional Extracted Images", ""])
            for name in unreferenced:
                suffix = Path(name).suffix or ".bin"
                filename = f"image-{len(image_records) + 1:03d}{suffix}"
                (images_dir / filename).write_bytes(zf.read(name))
                image_records[name] = filename
                md_lines.append(f"![{Path(name).name}](images/{filename})")
                md_lines.append("")

    markdown = "\n".join(md_lines)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"
    (out_dir / "ThucTap-566-HuynhNguyenTanPhat-LaiThuanPhat.md").write_text(markdown, encoding="utf-8")
    print(f"Wrote {out_dir}")
    print(f"Images: {len(image_records)}")


if __name__ == "__main__":
    main()
