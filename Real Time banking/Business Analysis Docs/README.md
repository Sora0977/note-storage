# Business Analysis Docs - Real-time Banking and Payment Risk Platform

Folder này đã được tách thành 2 nhóm tài liệu để dễ đọc:

- `PRD/`: mô tả sản phẩm, nghiệp vụ, actor, use case, scope và tiêu chí hoàn thành.
- `Tech Spec/`: mô tả thiết kế kỹ thuật, sequence diagram, data flow, data model, Kafka events và API.

## File nguồn đã đọc

- `Planning.md`
- `Resource.md`
- `Design system/Pattern.md`
- `Design system/Real_time_banking_payment_risk_platform_document.md`

## Cách đọc nhanh

1. Đọc [PRD/README.md](PRD/README.md)
   - Hiểu project đang giải quyết bài toán gì, ai dùng, MVP gồm gì, use case nào quan trọng.

2. Đọc [Tech Spec/README.md](<Tech Spec/README.md>)
   - Hiểu hệ thống chạy thế nào, service nào làm gì, Kafka event nào đi qua đâu, DB cần gì.
   - Xem thêm topology Docker Compose trong `Tech Spec/04_infrastructure_and_deployment.md`.

## Flow MVP chốt

```text
User A chuyển tiền cho User B
  -> kiểm tra idempotency
  -> kiểm tra fraud risk
  -> reserve/debit/credit wallet
  -> ghi double-entry ledger
  -> cập nhật transaction status
  -> bắn realtime notification lên dashboard
```

## Phạm vi nên giữ cho CV/demo

Ba phần không nên cắt khỏi MVP:

- Idempotency key chống double payment.
- Fraud risk check realtime.
- Double-entry ledger để audit dòng tiền.

Các phần như merchant payment, AML/KYT, settlement, reconciliation, manual review đầy đủ và external payment rail nên để phase 2/future improvements.
