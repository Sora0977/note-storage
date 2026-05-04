# Tech Spec - Technical Specification

Tech Spec trả lời câu hỏi: **hệ thống được thiết kế và implement như thế nào**.

## Tài liệu trong folder này

1. [01_sequence_diagrams.md](01_sequence_diagrams.md)
   - Happy path transfer.
   - Fraud reject path.
   - OTP challenge path.
   - Manual review path.
   - Idempotency retry.
   - Compensation khi credit/ledger fail.

2. [02_data_flow.md](02_data_flow.md)
   - Context data flow.
   - Event-driven transfer data flow.
   - Risk feature data flow.
   - Realtime dashboard data flow.
   - Data ownership.
   - Reliability flow với Outbox/Inbox.

3. [03_data_model_va_event_design.md](03_data_model_va_event_design.md)
   - Service responsibilities.
   - Database tối thiểu theo service.
   - Kafka topics.
   - Event envelope.
   - Event schema.
   - API tối thiểu.
   - Test case tối thiểu.

4. [04_infrastructure_and_deployment.md](04_infrastructure_and_deployment.md)
   - Docker Compose topology.
   - Container/service map.
   - Network, database schema, Kafka, Redis, observability.
   - Local deployment checklist.

## Tech Spec checklist trước khi code

- Chốt canonical Kafka topic/event names.
- Chốt transaction state machine.
- Chốt idempotency unique key: `(user_id, endpoint, idempotency_key)`.
- Chốt consumer dedupe theo message id và business command key.
- Chốt ledger posting key để chống ghi ledger trùng.
- Chốt API request/response tối thiểu.
- Chốt chuẩn error response theo RFC 7807 Problem Details.
- Chốt Saga recovery job cho transaction bị kẹt.
- Chốt test case cho idempotency, fraud, wallet, ledger, Saga, notification.
