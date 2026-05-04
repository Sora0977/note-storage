# PRD - Product Requirements Document

PRD trả lời câu hỏi: **project này làm gì, cho ai, giải quyết nghiệp vụ nào, scope MVP ra sao, khi nào được xem là xong**.

## Tài liệu trong folder này

1. [01_nghiep_vu_tong_quan.md](01_nghiep_vu_tong_quan.md)
   - Mục tiêu hệ thống.
   - Vấn đề nghiệp vụ.
   - Scope MVP và out of scope.
   - Actor/stakeholder.
   - Domain glossary.
   - Business capability.
   - Transaction lifecycle.
   - Risk decision policy.
   - Fraud rules.
   - Reconciliation glossary.
   - Definition of Done.

2. [02_use_cases.md](02_use_cases.md)
   - Use case overview.
   - Register/Login.
   - KYC giả lập.
   - Deposit demo money.
   - Create transfer.
   - Idempotent retry.
   - Fraud risk check.
   - OTP challenge.
   - Manual review.
   - Wallet reserve/debit/credit.
   - Double-entry ledger.
   - Realtime notification.

## PRD scope nên chốt

MVP nên được mô tả là:

```text
Internal wallet transfer risk demo
```

Không nên mô tả là core banking production đầy đủ. Mục tiêu chính là demo kỹ thuật backend/architecture cho CV.

## PRD checklist

- Có actor rõ.
- Có use case rõ.
- Có scope và out-of-scope.
- Có business rule quan trọng.
- Có trạng thái giao dịch.
- Có ghi rõ reconciliation là future improvement có chủ đích.
- Có acceptance/Definition of Done.
- Có điểm khác biệt để ghi CV: idempotency, fraud, Saga, ledger, realtime.
