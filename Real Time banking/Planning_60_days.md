# Planning 60 ngày - Real-time Banking and Payment Risk Platform

File này là kế hoạch 60 ngày để làm project `Real-time Banking and Payment Risk Platform` theo hướng portfolio/CV.

Mục tiêu không phải xây core banking production đầy đủ. Mục tiêu là làm một hệ thống demo đủ sâu để chứng minh bạn hiểu backend fintech, microservices, event-driven architecture, consistency, fraud risk, ledger và realtime monitoring.

## 1. Mục tiêu sau 60 ngày

Sau 60 ngày, project nên có:

- Source code chạy được bằng Docker Compose.
- React dashboard demo được end-to-end transfer flow.
- Spring Boot microservices có phân tách trách nhiệm rõ.
- API Gateway route request và kiểm tra JWT.
- Kafka event-driven flow cho transaction, fraud, wallet, ledger, notification.
- Idempotency key chống double payment.
- Saga flow có happy path, failure path và compensation cơ bản.
- Fraud risk check bằng rule engine đơn giản, có velocity rule.
- Wallet service có reserve, release, debit, credit và chống balance âm.
- Double-entry ledger có debit/credit, idempotent posting và audit được dòng tiền.
- Realtime notification qua WebSocket/STOMP.
- Transaction status history và audit log cơ bản.
- Outbox/Inbox hoặc consumer dedupe ở các service quan trọng.
- Observability cơ bản: correlation ID, structured logs, Zipkin, optional Grafana.
- Swagger/OpenAPI cho API chính.
- Test quan trọng cho idempotency, fraud, wallet, ledger, Saga.
- README, architecture diagram, sequence diagram, screenshots, demo video.
- CV bullets và phần giải thích phỏng vấn.

## 2. Scope chốt cho 60 ngày

Tên scope nên dùng:

```text
Internal wallet transfer risk platform
```

Không nên gọi là full banking system hoặc production payment gateway. Project tập trung vào một flow chính:

```text
User A chuyển tiền cho User B
  -> kiểm tra idempotency
  -> kiểm tra fraud risk
  -> reserve/debit/credit wallet
  -> ghi double-entry ledger
  -> cập nhật transaction status
  -> gửi realtime notification lên dashboard
```

## 3. Must-have scope

Đây là phần phải làm. Nếu thiếu các phần này thì project mất điểm khác biệt.

### Backend core

- `api-gateway`
  - Route request tới các service.
  - CORS.
  - JWT validation.
  - Correlation ID cho request.

- `auth-service`
  - Register.
  - Login.
  - Password hash.
  - JWT access token.
  - Role cơ bản: `USER`, `ADMIN`.

- `user-service`
  - User profile.
  - KYC giả lập: `PENDING`, `VERIFIED`, `BLOCKED`.
  - Admin verify user.
  - Chỉ user `VERIFIED` được chuyển tiền.

- `wallet-service`
  - Tạo wallet khi user verified.
  - Deposit demo money.
  - Get balance.
  - Reserve funds.
  - Release funds.
  - Debit sender.
  - Credit receiver.
  - Chống balance âm bằng optimistic locking hoặc SQL conditional update.

- `transaction-service`
  - Create transfer API.
  - Transaction state machine.
  - Idempotency key.
  - Saga orchestration.
  - Status history.
  - Failure reason.

- `fraud-service`
  - Rule-based fraud check.
  - Lưu fraud check result.
  - Publish risk decision event.
  - Blacklist receiver.

- `ledger-service`
  - Ghi double-entry ledger.
  - Mỗi completed transfer có đúng một debit và một credit.
  - Tổng debit bằng tổng credit.
  - Ledger entry immutable.
  - Posting key unique để chống ghi trùng.

- `notification-service`
  - Consume transaction/fraud/ledger events.
  - Lưu notification.
  - Push realtime qua WebSocket/STOMP.

### Frontend core

- Login page.
- Transfer form.
- Wallet balance.
- Transaction list.
- Transaction detail.
- Fraud alert realtime.
- Notification panel.
- Ledger entries theo transaction.

### Infra core

- Docker Compose chạy được:
  - PostgreSQL.
  - Kafka.
  - Redis.
  - Backend services.
  - Frontend.
  - Zipkin.
  - Kafka UI optional nhưng rất nên có để demo.

- Swagger/OpenAPI cho API chính.
- Seed data:
  - 2 user verified.
  - 1 user blocked hoặc receiver blacklist.
  - Wallet có balance demo.

## 4. Should-have scope

Đây là phần nên làm trong 60 ngày nếu core đã ổn. Các phần này làm project nhìn trưởng thành hơn rất nhiều.

- Redis velocity fraud:
  - Hơn 5 transfers trong 5 phút.
  - Tổng amount vượt ngưỡng trong 10 phút.
  - Gửi cho nhiều receiver trong thời gian ngắn.

- Outbox/Inbox hoặc consumer dedupe:
  - Outbox ở transaction-service.
  - Processed message table ở wallet-service, fraud-service, ledger-service.
  - Business key ổn định cho command/event.

- Saga recovery job:
  - Quét transaction kẹt ở `RISK_CHECKING`, `PROCESSING`, `COMPENSATING`.
  - Retry command idempotent hoặc mark `PENDING_REVIEW`.

- Audit log:
  - Ghi status change.
  - Ghi admin verify user.
  - Ghi blacklist action.

- Observability:
  - Correlation ID xuyên service.
  - Structured JSON logs.
  - Zipkin tracing.
  - Actuator health.
  - Prometheus/Grafana nếu còn thời gian.

- Testing:
  - Unit test fraud rules.
  - Unit test idempotency.
  - Unit test wallet balance.
  - Unit test ledger posting.
  - Integration test transfer success.
  - Integration test duplicate idempotency key.
  - Integration test fraud reject.
  - Integration test compensation.

- CI cơ bản:
  - GitHub Actions build backend.
  - Build frontend.
  - Run tests.
  - Optional Docker image build.

## 5. Could-have scope

Chỉ làm khi đã hoàn thành Must-have và phần lớn Should-have.

- OTP challenge giả lập:
  - Risk medium -> `CHALLENGE_REQUIRED`.
  - Gửi OTP giả lập qua notification.
  - Confirm OTP endpoint.
  - OTP passed -> tiếp tục Saga.
  - OTP failed/expired -> rejected.

- Manual review đơn giản:
  - Risk high -> `HELD_FOR_REVIEW`.
  - Admin/Analyst approve hoặc reject.
  - Lưu review note.
  - Không cần UI quá phức tạp.

- k6 load test nhẹ:
  - Baseline transfer.
  - Duplicate idempotency retry.
  - Concurrent debit same wallet.
  - Fraud velocity spike ở mức vừa phải, không cần 500 RPS nếu máy local yếu.

- Loki + Grafana logs.
- Rate limit ở gateway bằng Redis.
- Kafka Streams cho fraud velocity.
- Contract test/event schema validation.

## 6. Future improvement

Không nên làm trong 60 ngày trừ khi mọi thứ đã xong sớm.

- Kubernetes.
- Full CI/CD deploy lên VPS/cloud.
- External banking/payment gateway thật.
- PCI DSS production-grade.
- Multi-currency thật.
- Merchant payment.
- ML/AI fraud detection.
- Full reconciliation/end-of-day batch.
- Event sourcing full system.
- Admin portal đầy đủ.
- Role/permission phức tạp.
- Distributed transaction framework phức tạp.

## 7. Tech stack chốt

Backend:

- Java 21 hoặc Java 17.
- Spring Boot 3.
- Spring Security JWT.
- Spring Cloud Gateway.
- Spring Data JPA.
- PostgreSQL.
- Kafka.
- Redis.
- WebSocket/STOMP.
- OpenAPI/Swagger.
- Docker Compose.

Frontend:

- React.
- Vite.
- Axios.
- React Router.
- WebSocket/STOMP client.
- Chart/table library nếu cần.

Observability:

- Spring Boot Actuator.
- Micrometer.
- Zipkin.
- Prometheus + Grafana optional.
- Loki + Promtail optional.

Testing:

- JUnit 5.
- Mockito.
- Testcontainers nếu còn thời gian.
- k6 optional.

## 8. Architecture cuối cùng

Services:

- `api-gateway`
- `auth-service`
- `user-service`
- `wallet-service`
- `transaction-service`
- `fraud-service`
- `ledger-service`
- `notification-service`

Optional:

- `audit-service`: chỉ tách riêng nếu còn thời gian. Nếu không, để audit trong transaction-service hoặc từng service.
- `case-service`: chỉ làm nếu chọn manual review. Nếu không, giữ review case trong fraud-service.

Infra:

- PostgreSQL.
- Kafka.
- Redis.
- Zipkin.
- Kafka UI.
- Docker Compose.
- Prometheus/Grafana optional.
- Loki/Promtail optional.

## 9. Kafka topic nên chốt

Must-have topics:

- `transaction.created`
- `fraud.passed`
- `fraud.rejected`
- `wallet.reserve.command`
- `wallet.reserved`
- `wallet.reserve_failed`
- `wallet.debit.command`
- `wallet.debited`
- `wallet.credit.command`
- `wallet.credited`
- `wallet.compensate.command`
- `wallet.compensated`
- `ledger.record.command`
- `ledger.recorded`
- `ledger.record_failed`
- `transaction.completed`
- `transaction.failed`
- `notification.created`

Could-have topics:

- `risk.challenge_required`
- `risk.hold_required`
- `challenge.passed`
- `challenge.failed`
- `review.approved`
- `review.rejected`

## 10. Transaction status chốt

Must-have:

- `PENDING`
- `RISK_CHECKING`
- `APPROVED`
- `REJECTED`
- `PROCESSING`
- `COMPLETED`
- `FAILED`
- `COMPENSATING`
- `COMPENSATED`
- `PENDING_REVIEW`

Could-have:

- `CHALLENGE_REQUIRED`
- `HELD_FOR_REVIEW`

Quy tắc:

- `COMPLETED` không được quay lại `PENDING`.
- `REJECTED` là terminal state.
- `FAILED` có thể sang `COMPENSATING`.
- `COMPENSATING` thành công thì sang `COMPENSATED`.
- Compensation fail nhiều lần thì sang `PENDING_REVIEW`.

## 11. Fraud rules nên implement

### Level 1 - bắt buộc

- Sender KYC chưa verified -> reject.
- Receiver blacklisted -> reject.
- Amount lớn hơn ngưỡng, ví dụ `50,000,000 VND` -> risk score cao.
- Insufficient balance -> wallet failure, không phải fraud, nhưng phải hiện reason rõ.

### Level 2 - nên có

- Sender gửi hơn 5 giao dịch trong 5 phút.
- Tổng số tiền sender gửi vượt `100,000,000 VND` trong 10 phút.
- Sender gửi cho hơn 3 receiver trong 10 phút.

### Level 3 - optional

- Device fingerprint mới.
- New beneficiary.
- User risk profile.
- Geo-location mismatch giả lập.

## 12. Saga flow nên implement

### Happy path

1. Client gọi `POST /transfers` với `Idempotency-Key`.
2. transaction-service validate request.
3. transaction-service lưu idempotency record.
4. transaction-service tạo transaction `PENDING`.
5. transaction-service publish `transaction.created`.
6. fraud-service consume event và check rules.
7. fraud-service publish `fraud.passed`.
8. transaction-service chuyển status sang `APPROVED`.
9. transaction-service publish `wallet.reserve.command`.
10. wallet-service reserve funds.
11. wallet-service publish `wallet.reserved`.
12. transaction-service publish `wallet.debit.command`.
13. wallet-service debit sender.
14. wallet-service publish `wallet.debited`.
15. transaction-service publish `wallet.credit.command`.
16. wallet-service credit receiver.
17. wallet-service publish `wallet.credited`.
18. transaction-service publish `ledger.record.command`.
19. ledger-service ghi debit/credit.
20. ledger-service publish `ledger.recorded`.
21. transaction-service mark `COMPLETED`.
22. notification-service push realtime success.

### Fraud reject path

1. transaction-service publish `transaction.created`.
2. fraud-service detect blacklist/KYC/critical risk.
3. fraud-service publish `fraud.rejected`.
4. transaction-service mark `REJECTED`.
5. notification-service push fraud alert.
6. wallet-service không được debit/credit.

### Wallet failure path

1. fraud passed.
2. wallet reserve fail vì insufficient balance hoặc wallet frozen.
3. wallet-service publish `wallet.reserve_failed`.
4. transaction-service mark `FAILED`.
5. notification-service push failure reason.

### Compensation path

1. Debit sender thành công.
2. Credit receiver hoặc ledger fail.
3. transaction-service publish `wallet.compensate.command`.
4. wallet-service hoàn tác tiền bằng release/refund/reversal.
5. transaction-service mark `COMPENSATED` hoặc `PENDING_REVIEW`.
6. notification-service push failure/compensation status.

## 13. Database tối thiểu

auth-service:

- `users`
- `roles`
- `user_roles`
- `refresh_tokens` optional

user-service:

- `user_profiles`

wallet-service:

- `wallets`
- `wallet_holds`
- `wallet_transactions`
- `processed_messages`

transaction-service:

- `transactions`
- `transaction_status_history`
- `idempotency_keys`
- `outbox_events`
- `processed_messages`
- `audit_logs` nếu không tách audit-service

fraud-service:

- `fraud_rules`
- `fraud_checks`
- `blacklist_accounts`
- `processed_messages`
- `risk_cases` optional

ledger-service:

- `ledger_entries`
- `processed_messages`

notification-service:

- `notifications`

## 14. API tối thiểu

Auth:

- `POST /auth/register`
- `POST /auth/login`

User:

- `GET /users/me`
- `PATCH /users/{id}/verify`

Wallet:

- `POST /wallets/deposit`
- `GET /wallets/me`
- `GET /wallets/me/transactions`

Transaction:

- `POST /transfers`
- `GET /transfers`
- `GET /transfers/{id}`

Fraud:

- `GET /fraud/checks`
- `GET /fraud/checks/{transactionId}`
- `PATCH /fraud/blacklist/{userId}`

Ledger:

- `GET /ledger/entries`
- `GET /ledger/entries/{transactionId}`

Notification:

- `GET /notifications`
- `WebSocket /ws`

Optional:

- `POST /transfers/{id}/confirm-otp`
- `POST /risk-cases/{id}/approve`
- `POST /risk-cases/{id}/reject`

## 15. Kế hoạch 60 ngày theo phase

## Phase 1 - Ngày 1 đến 15: Foundation

Mục tiêu:

- Chốt architecture.
- Dựng repo.
- Chạy được infra local.
- Có gateway, auth, user, wallet basic.

Deliverable cuối phase:

- Docker Compose chạy PostgreSQL, Kafka, Redis.
- Backend services skeleton chạy được.
- Health endpoint cho mỗi service.
- Gateway route được tới auth/user/wallet/transaction.
- Auth login trả JWT.
- User KYC verified tạo được wallet.
- Wallet deposit và get balance chạy được.

### Ngày 1: Chốt scope và architecture

- Đọc lại PRD và Tech Spec.
- Chốt flow MVP.
- Chốt service list.
- Chốt topic list.
- Chốt transaction status.
- Vẽ architecture diagram bản đầu.

Output:

- README draft.
- Architecture diagram.
- Scope Must/Should/Could/Future.

### Ngày 2: Setup repo

- Tạo repo.
- Chọn monorepo hoặc Maven multi-module.
- Tạo folder backend/frontend/infra/docs.
- Tạo common-lib cho DTO/event/error nếu cần.

Output:

- Project structure rõ ràng.
- README có cách setup dev.

### Ngày 3: Docker Compose infra

- PostgreSQL.
- Kafka.
- Redis.
- Kafka UI.
- Zipkin.

Output:

- `docker compose up` chạy được infra.
- Kafka topic tạo tự động hoặc có script tạo topic.

### Ngày 4: Service skeleton

- Tạo skeleton cho gateway, auth, user, wallet, transaction, fraud, ledger, notification.
- Thêm Actuator health.
- Thêm profile dev/docker.

Output:

- Mỗi service start được.
- Health endpoint xanh.

### Ngày 5: API Gateway

- Route tới auth/user/wallet/transaction.
- CORS.
- Global error format draft.
- Correlation ID filter.

Output:

- Frontend/backend gọi qua gateway.

### Ngày 6: Auth service

- Register.
- Login.
- Password hash.
- JWT.
- Role `USER`, `ADMIN`.

Output:

- Login trả access token.

### Ngày 7: Security integration

- Gateway validate JWT.
- Forward user id/role header nội bộ.
- Chặn endpoint cần auth.

Output:

- API protected hoạt động qua gateway.

### Ngày 8: User service

- User profile.
- KYC status.
- Admin verify user.

Output:

- User verified được.

### Ngày 9: Wallet basic

- Tạo wallet.
- Deposit demo money.
- Get balance.
- Wallet status.

Output:

- Có balance demo.

### Ngày 10: Wallet transaction history

- Lưu wallet transaction.
- API lịch sử ví.
- Validation amount.

Output:

- Xem được lịch sử deposit.

### Ngày 11: Frontend setup

- React Vite.
- Routing.
- Login page.
- API client.
- Auth token storage.

Output:

- Login UI dùng được.

### Ngày 12: Frontend wallet/profile

- Profile page.
- Wallet balance.
- Deposit demo page hoặc action.

Output:

- Demo login -> xem ví.

### Ngày 13: OpenAPI và seed data

- Swagger cho auth/user/wallet.
- Seed users và wallets.

Output:

- Người khác chạy lên có data demo.

### Ngày 14: Review foundation

- Fix lỗi compose.
- Chuẩn hóa README.
- Commit sạch.

Output:

- Phase 1 demo được.

### Ngày 15: Buffer

- Dành cho bug, setup chậm, hoặc refactor.

## Phase 2 - Ngày 16 đến 30: Transfer, Kafka, Idempotency, Saga happy path

Mục tiêu:

- Tạo transfer.
- Chống duplicate payment.
- Có Kafka event flow.
- Có fraud approve/reject cơ bản.
- Có wallet money movement qua Saga happy path.

Deliverable cuối phase:

- Create transfer qua API.
- Duplicate `Idempotency-Key` không tạo transaction thứ hai.
- Kafka flow chạy transaction -> fraud -> transaction.
- Wallet reserve/debit/credit chạy qua command/event.
- Transaction completed/rejected/failed có status rõ.

### Ngày 16: Transaction model

- Entity `transactions`.
- Status enum.
- API `POST /transfers`.
- API list/detail.

Output:

- Tạo transaction `PENDING`.

### Ngày 17: Idempotency key

- Header `Idempotency-Key`.
- Unique key `(user_id, endpoint, idempotency_key)`.
- Request hash.
- Same key same body trả response cũ.
- Same key different body trả `409`.

Output:

- Gửi 2 lần không tạo 2 transaction.

### Ngày 18: Kafka event envelope

- Chuẩn event envelope.
- Producer config.
- Consumer config.
- Correlation ID trong event.

Output:

- Publish/consume event mẫu được.

### Ngày 19: transaction.created

- transaction-service publish `transaction.created`.
- fraud-service consume event.
- notification-service log event trước.

Output:

- Tạo transfer sinh Kafka event.

### Ngày 20: Fraud Level 1

- KYC not verified.
- Receiver blacklist.
- Amount threshold.
- Lưu fraud check.
- Publish `fraud.passed` hoặc `fraud.rejected`.

Output:

- Transfer low-risk pass.
- Blacklisted receiver bị reject.

### Ngày 21: Transaction status update

- transaction-service consume fraud event.
- Update status `APPROVED` hoặc `REJECTED`.
- Ghi status history.

Output:

- Xem detail thấy status thay đổi.

### Ngày 22: Wallet reserve command

- transaction-service publish `wallet.reserve.command`.
- wallet-service reserve funds.
- Optimistic locking hoặc SQL conditional update.

Output:

- Reserve không làm balance âm.

### Ngày 23: Wallet debit/credit

- Debit sender.
- Credit receiver.
- Publish `wallet.debited`, `wallet.credited`.

Output:

- Balance sender/receiver update đúng.

### Ngày 24: Saga happy path

- Orchestrate fraud -> reserve -> debit -> credit.
- Mark `COMPLETED` tạm thời sau credit.

Output:

- Transfer completed bằng event flow.

### Ngày 25: Failure path cơ bản

- Insufficient balance.
- Wallet frozen.
- Fraud reject.
- Mark `FAILED` hoặc `REJECTED`.

Output:

- Demo failure reason rõ.

### Ngày 26: Frontend transfer form

- Form tạo transfer.
- Gửi idempotency key từ client.
- Show status ban đầu.

Output:

- Tạo transfer từ UI.

### Ngày 27: Transaction list/detail UI

- List transaction.
- Detail status.
- Failure reason.

Output:

- Demo UI thấy transaction lifecycle.

### Ngày 28: Integration test lần 1

- Transfer success.
- Duplicate idempotency key.
- Fraud reject.
- Insufficient balance.

Output:

- Có test cơ bản cho phase 2.

### Ngày 29: Refactor phase 2

- Chuẩn hóa error response.
- Chuẩn hóa event names.
- Update Swagger.

Output:

- Flow ổn định hơn.

### Ngày 30: Demo checkpoint 1

Demo được:

- Login.
- Deposit.
- Create transfer.
- Duplicate idempotency key.
- Fraud reject.
- Wallet balance update.
- Kafka UI thấy event.

## Phase 3 - Ngày 31 đến 45: Ledger, compensation, realtime dashboard, reliability

Mục tiêu:

- Thêm double-entry ledger.
- Thêm compensation.
- Thêm WebSocket realtime.
- Thêm fraud velocity.
- Thêm outbox/inbox hoặc consumer dedupe.

Deliverable cuối phase:

- Transfer completed có ledger debit/credit.
- Ledger command publish lại không ghi trùng.
- Credit/ledger fail có compensation.
- Dashboard nhận notification realtime.
- Fraud velocity rule hoạt động.

### Ngày 31: Ledger model

- `ledger_entries`.
- Posting key.
- Debit/credit entry.
- Immutable rule.

Output:

- Ledger service ghi entry được.

### Ngày 32: Ledger integration

- transaction-service publish `ledger.record.command`.
- ledger-service consume và ghi ledger.
- Publish `ledger.recorded`.

Output:

- Completed transfer có ledger.

### Ngày 33: Ledger idempotency

- Unique `posting_key`.
- Duplicate command không tạo posting trùng.
- API query ledger by transaction.

Output:

- Ledger an toàn khi Kafka retry.

### Ngày 34: Transaction complete after ledger

- Chỉ mark `COMPLETED` sau `ledger.recorded`.
- Notification consume `transaction.completed`.

Output:

- Status lifecycle đúng hơn.

### Ngày 35: Compensation design

- Chốt compensation rules.
- Tạo event/command compensation.
- Ghi failure reason.

Output:

- Có skeleton compensation.

### Ngày 36: Compensation implementation

- Credit fail -> compensate debit/reserve.
- Ledger fail -> compensate hoặc mark `PENDING_REVIEW`.
- Publish `wallet.compensate.command`.

Output:

- Demo rollback cơ bản.

### Ngày 37: Saga recovery job

- Quét transaction kẹt.
- Retry command idempotent hoặc mark `PENDING_REVIEW`.

Output:

- Không bị kẹt silent quá lâu.

### Ngày 38: Processed messages

- `processed_messages` cho wallet/fraud/ledger.
- Dedupe theo `message_id` và `business_key`.

Output:

- Consumer xử lý trùng an toàn hơn.

### Ngày 39: Outbox transaction-service

- Lưu outbox event cùng DB transaction.
- Publisher job publish event.
- Mark published/failed.

Output:

- Transaction create và event publish đáng tin hơn.

### Ngày 40: Fraud velocity với Redis

- Count transfer by sender trong 5 phút.
- Sum amount trong 10 phút.
- Many receivers trong 10 phút.

Output:

- Spam transfer trigger risk rule.

### Ngày 41: Notification service

- Notification table.
- Consume transaction/fraud events.
- REST list notifications.

Output:

- Có lịch sử notification.

### Ngày 42: WebSocket/STOMP

- `/ws`.
- Topic theo user hoặc global demo.
- Push transaction completed/failed/fraud alert.

Output:

- Client nhận realtime event.

### Ngày 43: Realtime dashboard

- Notification panel.
- Fraud alert.
- Transaction status tự update.

Output:

- Demo UI không cần refresh.

### Ngày 44: Audit log

- Status change audit.
- Admin verify audit.
- Blacklist audit.

Output:

- Trace được lịch sử nghiệp vụ.

### Ngày 45: Demo checkpoint 2

Demo được:

- Transfer success có ledger.
- Fraud velocity alert.
- Compensation case.
- WebSocket realtime alert.
- Ledger query.
- Audit/status history.

## Phase 4 - Ngày 46 đến 60: Polish, testing, observability, docs, CV

Mục tiêu:

- Biến project từ "chạy được" thành "đáng đưa vào CV".
- Tăng test coverage ở phần rủi ro cao.
- Làm docs, demo video và CV bullet.

Deliverable cuối phase:

- Docker Compose one-command run.
- README chuyên nghiệp.
- Swagger mở được.
- Zipkin/correlation ID hoạt động.
- Test quan trọng pass.
- Demo video 3-5 phút.
- CV bullets sẵn dùng.

### Ngày 46: Observability core

- Correlation ID xuyên gateway/service/event.
- Structured logs.
- Actuator health.

Output:

- Trace/debug dễ hơn.

### Ngày 47: Zipkin tracing

- Gateway -> transaction -> fraud -> wallet -> ledger.
- Trace ID trong logs.

Output:

- Xem được request/event flow.

### Ngày 48: Metrics optional

- Micrometer.
- Prometheus scrape.
- Grafana dashboard nếu còn thời gian.

Output:

- Có screenshot observability nếu làm kịp.

### Ngày 49: Error handling

- RFC 7807 Problem Details.
- Error code chuẩn.
- Failure reason rõ.

Output:

- API/UI dễ hiểu lỗi.

### Ngày 50: Unit tests

- Fraud rules.
- Idempotency.
- Wallet reserve/debit.
- Ledger posting.

Output:

- Unit test cho logic quan trọng.

### Ngày 51: Integration tests

- Transfer success.
- Duplicate idempotency key.
- Fraud reject.
- Insufficient balance.

Output:

- Flow chính có test.

### Ngày 52: Saga/ledger tests

- Credit fail -> compensation.
- Ledger command duplicate.
- Completed transaction có debit/credit.

Output:

- Money correctness được chứng minh.

### Ngày 53: Security polish

- JWT validation ở gateway.
- Role-based endpoint.
- Không expose internal endpoints qua frontend.
- Validate amount/currency.

Output:

- API không bị gọi bừa dễ dàng.

### Ngày 54: CI cơ bản

- GitHub Actions:
  - Build backend.
  - Build frontend.
  - Run tests.
- Docker build optional.

Output:

- Badge hoặc screenshot CI.

### Ngày 55: Load test nhẹ optional

- k6 script cho transfer.
- Idempotency retry storm nhỏ.
- Concurrent debit same wallet nhỏ.

Output:

- Có số liệu demo nếu máy chịu được.

### Ngày 56: README chuyên nghiệp

README cần có:

- Project overview.
- Problem solved.
- Architecture diagram.
- Tech stack.
- Service list.
- Event flow.
- Database design.
- How to run.
- API docs.
- Demo accounts.
- Screenshots.
- Demo video link.
- What I learned.
- Future improvements.

Output:

- README đủ để recruiter/interviewer đọc.

### Ngày 57: Diagrams và screenshots

- Architecture diagram.
- Sequence diagram happy path.
- Sequence diagram fraud reject.
- Screenshot dashboard.
- Screenshot Kafka UI.
- Screenshot Zipkin/Grafana nếu có.

Output:

- README có hình minh họa.

### Ngày 58: Demo script và video

Video 3-5 phút:

1. Giới thiệu problem.
2. Show architecture.
3. Login.
4. Deposit demo money.
5. Transfer success.
6. Show ledger debit/credit.
7. Duplicate idempotency key.
8. Fraud blacklist hoặc velocity alert.
9. Realtime WebSocket notification.
10. Show Zipkin/Kafka UI.

Output:

- Video demo sẵn để đưa vào GitHub/CV.

### Ngày 59: Final cleanup

- Xóa code thừa.
- Chuẩn hóa package.
- Check Docker Compose chạy từ đầu.
- Check seed data.
- Check README trên máy sạch nếu có thể.

Output:

- Repo sạch.

### Ngày 60: CV và interview prep

- Viết CV bullet.
- Viết GitHub pinned repo description.
- Viết LinkedIn post.
- Chuẩn bị câu trả lời phỏng vấn:
  - Vì sao dùng idempotency?
  - Saga khác DB transaction thế nào?
  - Vì sao cần double-entry ledger?
  - Làm sao chống Kafka duplicate?
  - Làm sao tránh wallet âm?
  - Nếu ledger fail sau debit thì xử lý thế nào?

Output:

- Package portfolio hoàn chỉnh.

## 16. Milestone kiểm tra

### Sau ngày 15

Bạn phải demo được:

- Docker Compose infra chạy.
- Gateway route API.
- Register/login.
- JWT.
- Verify KYC.
- Deposit.
- Wallet balance.
- Swagger cho API cơ bản.

### Sau ngày 30

Bạn phải demo được:

- Create transfer.
- Idempotency key.
- Kafka event flow.
- Fraud approve/reject Level 1.
- Wallet reserve/debit/credit.
- Transaction status update.
- Transaction list/detail UI.

### Sau ngày 45

Bạn phải demo được:

- Ledger debit/credit.
- Ledger idempotent posting.
- Compensation case.
- Fraud velocity rule.
- WebSocket realtime alert.
- Audit/status history.
- Dashboard usable.

### Sau ngày 60

Bạn phải có:

- End-to-end demo hoàn chỉnh.
- Docker Compose one-command run.
- README đầy đủ.
- Swagger.
- Tests quan trọng.
- Zipkin/correlation ID.
- Screenshots.
- Demo video.
- CV bullets.

## 17. Lịch làm mỗi ngày

Nếu bạn có 6-8 giờ/ngày:

- 1 giờ đọc resource hoặc đọc docs liên quan trực tiếp.
- 4-5 giờ code.
- 1 giờ test/debug.
- 30 phút docs/README.
- 30 phút ghi lại issue và plan ngày sau.

Nếu bạn có 10-12 giờ/ngày:

- 1.5 giờ học/resource.
- 7-8 giờ code.
- 1 giờ test.
- 1 giờ docs.
- 30 phút refactor.
- 30 phút plan ngày sau.

Rule quan trọng:

- Mỗi ngày phải có output commit được.
- Không học lan man quá 2 giờ nếu chưa code.
- Không nhảy sang feature mới khi flow cũ chưa demo được.
- Luôn giữ Docker Compose chạy được.

## 18. Thứ tự ưu tiên nếu bị trễ

Cắt theo thứ tự này:

1. Kubernetes.
2. External gateway/payment thật.
3. ML fraud.
4. Merchant payment.
5. Full reconciliation/end-of-day.
6. Admin portal đầy đủ.
7. Manual review UI.
8. OTP challenge.
9. Loki/Promtail/Grafana logs.
10. Prometheus/Grafana metrics.
11. k6 load test.
12. CI/CD push registry/deploy.
13. Kafka Streams, thay bằng Redis/DB query.
14. Audit-service riêng, gộp audit vào transaction-service.
15. Outbox đầy đủ ở mọi service, giữ ít nhất consumer dedupe/processed_messages.

Không cắt:

- Idempotency.
- Fraud risk check.
- Wallet reserve/debit/credit.
- Kafka event flow.
- Double-entry ledger.
- Realtime notification.
- Docker Compose.
- README/demo video.

## 19. Definition of Done

Project được xem là xong khi:

- Người khác clone repo và chạy `docker compose up` được.
- UI demo được transfer thành công.
- Duplicate request với cùng `Idempotency-Key` không tạo giao dịch trùng.
- Transfer high-risk bị reject hoặc flag rõ reason.
- Wallet không âm.
- Completed transfer có đúng debit và credit ledger.
- Ledger command duplicate không tạo posting trùng.
- Kafka event flow chạy qua nhiều service.
- WebSocket push realtime alert/status.
- Transaction status history đọc được.
- Swagger mở được.
- Có ít nhất 12 test quan trọng.
- README có architecture, setup, API, screenshots.
- Có demo video 3-5 phút.
- Có CV bullets rõ tác động kỹ thuật.

## 20. CV bullet cuối

Sau khi hoàn thành, có thể dùng:

- Built a real-time banking and payment risk platform using Spring Boot microservices, Kafka, PostgreSQL, Redis, WebSocket, Docker Compose, and Spring Cloud Gateway.
- Implemented idempotent wallet transfers, Saga-based transaction orchestration, fraud risk checks, realtime notifications, and transaction status tracking.
- Designed a double-entry ledger with idempotent posting keys to preserve money movement integrity across distributed services.
- Added consumer deduplication, compensation handling, correlation IDs, distributed tracing, API documentation, and a React dashboard for live transaction monitoring.
- Created Docker Compose deployment, automated seed data, focused tests, architecture documentation, and a demo video for portfolio presentation.

## 21. Câu trả lời phỏng vấn nên chuẩn bị

- Vì sao payment API cần idempotency key?
- Nếu client gửi cùng idempotency key nhưng body khác thì xử lý thế nào?
- Kafka có thể deliver duplicate message, service của bạn chống duplicate ra sao?
- Vì sao không chỉ update balance mà cần double-entry ledger?
- Wallet service chống balance âm thế nào khi nhiều request đồng thời?
- Saga khác distributed transaction 2PC thế nào?
- Nếu debit sender thành công nhưng credit receiver fail thì xử lý thế nào?
- Nếu ledger fail sau khi wallet đã update thì trạng thái transaction nên là gì?
- Fraud velocity rule dùng Redis/Kafka Streams như thế nào?
- Vì sao observability quan trọng trong microservices?

## 22. Kết luận scope

60 ngày là đủ để làm project này ở mức mạnh nếu bạn giữ đúng trọng tâm:

```text
Transfer correctness + fraud risk + ledger integrity + realtime visibility
```

Đừng để project biến thành banking system quá lớn. Phần ăn điểm nhất không phải số lượng feature, mà là bạn chứng minh được những vấn đề khó trong payment:

- Không trừ tiền lặp.
- Không để ví âm.
- Không mất dấu dòng tiền.
- Không xử lý Kafka message trùng thành tiền thật.
- Khi service fail vẫn có trạng thái rõ và có hướng recovery.
- Dashboard nhìn được hệ thống chạy realtime.
