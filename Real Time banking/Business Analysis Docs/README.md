# Business Analysis Docs - Real-time Banking and Payment Risk Platform

Folder này gom lại nghiệp vụ và các sơ đồ chính từ toàn bộ tài liệu trong thư mục `Real Time banking`.

## File nguồn đã đọc

- `Planning.md`
- `Resource.md`
- `Design system/Pattern.md`
- `Design system/Real_time_banking_payment_risk_platform_document.md`

## Thứ tự đọc gợi ý

1. `01_nghiep_vu_tong_quan.md`
   - Bối cảnh nghiệp vụ, phạm vi MVP, actor, domain glossary, lifecycle, risk decision.

2. `02_use_cases.md`
   - Use case tổng quan và mô tả từng use case chính theo actor.

3. `03_sequence_diagrams.md`
   - Sequence diagram cho transfer thành công, fraud reject, OTP challenge, manual review, idempotency retry, compensation.

4. `04_data_flow.md`
   - Dataflow cấp hệ thống, event-driven flow, risk feature flow, dashboard realtime flow.

5. `05_data_model_va_event_design.md`
   - Service responsibility, database tối thiểu, Kafka topics, event schema, API tối thiểu.

## Cách nhìn nhanh project

Project nên tập trung vào một flow chính trước:

```text
User A chuyển tiền cho User B
  -> kiểm tra idempotency
  -> kiểm tra fraud risk
  -> reserve/debit/credit wallet
  -> ghi double-entry ledger
  -> cập nhật transaction status
  -> bắn realtime notification lên dashboard
```

Ba phần không nên cắt khỏi MVP:

- Idempotency key chống double payment.
- Fraud risk check realtime.
- Double-entry ledger để audit dòng tiền.
