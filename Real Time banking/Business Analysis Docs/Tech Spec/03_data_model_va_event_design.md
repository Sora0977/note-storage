# 03. Data model và event design

## 1. Service responsibilities

| Service | Trách nhiệm |
|---|---|
| api-gateway | Routing, JWT validation, CORS, rate limit, correlation id |
| auth-service | Register, login, password hash, JWT, role |
| user-service | User profile, KYC status, admin verify user |
| wallet-service | Wallet, deposit, reserve, release, debit, credit, balance view. Dùng optimistic locking với cột `version` và điều kiện `available_balance >= amount` ngay trong SQL update để tránh race condition |
| transaction-service | Transfer API, idempotency, transaction state machine, Saga orchestration, Saga recovery job |
| fraud-service | Fraud rules, velocity checks, risk score, blacklist, fraud checks |
| ledger-service | Double-entry ledger, reversal entry nếu cần, ledger query |
| notification-service | Kafka event consumer, notification table, WebSocket push |
| audit-service optional | Audit log cho admin action, analyst decision, status change |

## 2. Database tối thiểu theo service

### auth-service

```text
users
- id
- email
- password_hash
- status
- created_at
- updated_at

roles
- id
- name

user_roles
- user_id
- role_id

refresh_tokens optional
- id
- user_id
- token_hash
- expires_at
- revoked_at
```

### user-service

```text
user_profiles
- id
- auth_user_id
- full_name
- phone
- kyc_status: PENDING, VERIFIED, BLOCKED
- created_at
- updated_at
```

### transaction-service

```text
transactions
- id
- sender_id
- receiver_id
- amount
- currency
- status
- risk_score
- risk_decision
- failure_reason
- saga_step
- compensation_status
- review_case_id
- challenge_id
- approved_by
- reviewed_by
- review_note
- resolved_at
- created_at
- updated_at

transaction_status_history
- id
- transaction_id
- old_status
- new_status
- reason
- created_at

idempotency_keys
- id
- user_id
- endpoint
- idempotency_key
- request_hash
- response_body
- status_code
- transaction_id
- created_at
- expires_at

Unique constraint:
- (user_id, endpoint, idempotency_key)

outbox_events
- id
- aggregate_type
- aggregate_id
- event_type
- payload
- status: NEW, PUBLISHED, FAILED
- created_at
- published_at

processed_messages
- id
- message_id
- business_key
- consumer_name
- processed_at

Unique constraints:
- (message_id, consumer_name)
- (business_key, consumer_name)
```

### wallet-service

```text
wallets
- id
- user_id
- currency
- available_balance
- reserved_balance
- status: ACTIVE, FROZEN, CLOSED
- version
- created_at
- updated_at

Concurrency rule:
- Reserve/debit phải dùng optimistic locking qua `version`.
- Reserve phải kiểm tra `available_balance >= amount` trong cùng câu SQL update.
- Nếu update count = 0, trả lỗi `INSUFFICIENT_FUNDS` hoặc `WALLET_CONCURRENT_UPDATE`.
- Không đọc balance rồi update bằng 2 câu tách rời nếu không có lock/version.

SQL pattern gợi ý:

```sql
UPDATE wallets
SET available_balance = available_balance - :amount,
    reserved_balance = reserved_balance + :amount,
    version = version + 1,
    updated_at = now()
WHERE id = :wallet_id
  AND version = :expected_version
  AND available_balance >= :amount
  AND status = 'ACTIVE';
```

Nếu số dòng update bằng `0`, service phải reload wallet để phân biệt không đủ tiền, wallet bị khóa, hoặc concurrent update.

wallet_holds
- id
- transaction_id
- wallet_id
- amount
- status: HELD, RELEASED, CAPTURED
- expires_at
- created_at
- updated_at

wallet_transactions
- id
- transaction_id
- wallet_id
- entry_type: DEPOSIT, RESERVE, RELEASE, DEBIT, CREDIT, REVERSAL
- amount
- balance_after
- created_at

processed_messages
- id
- message_id
- business_key
- consumer_name
- processed_at
```

### fraud-service

```text
fraud_rules
- id
- code
- name
- condition_json
- score
- active
- version
- created_at
- updated_at

fraud_checks
- id
- transaction_id
- sender_id
- receiver_id
- amount
- risk_score
- decision: APPROVE, CHALLENGE, HOLD, DECLINE
- reasons_json
- reviewed_by
- review_note
- reviewed_at
- created_at

risk_cases optional cho Phase 2 hoặc nếu làm HOLD:
- id
- transaction_id
- status: OPEN, ASSIGNED, APPROVED, REJECTED, CLOSED
- priority
- assigned_to
- decision
- reason_code
- analyst_note
- created_at
- closed_at

blacklist_accounts
- id
- user_id
- reason
- active
- created_at

processed_messages
- id
- message_id
- business_key
- consumer_name
- processed_at
```

### ledger-service

```text
ledger_entries
- id
- posting_id
- posting_key
- transaction_id
- wallet_id
- entry_type: DEBIT, CREDIT, REVERSAL_DEBIT, REVERSAL_CREDIT
- amount
- currency
- balance_before
- balance_after
- reversal_of_entry_id
- created_at

processed_messages
- id
- message_id
- business_key
- consumer_name
- processed_at
```

Rule bắt buộc:

```text
sum(DEBIT) = sum(CREDIT) for each completed transaction
```

Ledger không update/xóa entry cũ. Nếu cần sửa sai, tạo reversal entry.

Ledger idempotency:

- `posting_key` nên unique theo business operation, ví dụ `transaction:{transactionId}:settlement`.
- Một transaction completed chỉ được ghi một posting settlement.
- Nếu cần rollback, tạo posting reversal mới và liên kết bằng `reversal_of_entry_id`.

### notification-service

```text
notifications
- id
- user_id
- transaction_id
- type
- title
- message
- read_at
- created_at
```

## 3. Kafka topics

| Topic | Producer | Consumer | Mục đích |
|---|---|---|---|
| transaction.created | transaction-service | fraud-service, notification-service | Bắt đầu risk check |
| fraud.passed | fraud-service | transaction-service | Cho phép xử lý tiền |
| fraud.rejected | fraud-service | transaction-service, notification-service | Từ chối vì fraud |
| risk.challenge_required | fraud-service | transaction-service, notification-service | Cần OTP |
| risk.hold_required | fraud-service | transaction-service, case-service | Cần analyst review |
| wallet.reserve.command | transaction-service | wallet-service | Giữ tiền |
| wallet.reserved | wallet-service | transaction-service | Giữ tiền thành công |
| wallet.reserve_failed | wallet-service | transaction-service | Không đủ tiền/lỗi giữ tiền |
| wallet.debit.command | transaction-service | wallet-service | Trừ tiền sender |
| wallet.debited | wallet-service | transaction-service | Debit thành công |
| wallet.credit.command | transaction-service | wallet-service | Cộng tiền receiver |
| wallet.credited | wallet-service | transaction-service | Credit thành công |
| wallet.compensate.command | transaction-service | wallet-service | Hoàn tác tiền |
| wallet.compensated | wallet-service | transaction-service | Hoàn tác xong |
| ledger.record.command | transaction-service | ledger-service | Ghi ledger |
| ledger.recorded | ledger-service | transaction-service, notification-service | Ledger ghi xong |
| ledger.record_failed | ledger-service | transaction-service | Ledger lỗi |
| transaction.completed | transaction-service | notification-service, dashboard | Giao dịch hoàn thành |
| transaction.failed | transaction-service | notification-service, dashboard | Giao dịch thất bại |
| notification.created | notification-service | dashboard optional | Notification mới |

## 4. Event envelope chuẩn

```json
{
  "eventId": "evt_001",
  "eventType": "transaction.created",
  "occurredAt": "2026-05-04T10:00:00Z",
  "correlationId": "corr_001",
  "causationId": "cmd_001",
  "aggregateType": "transaction",
  "aggregateId": "txn_001",
  "payload": {}
}
```

## 5. Event schema gợi ý

### transaction.created

```json
{
  "eventId": "evt_001",
  "eventType": "transaction.created",
  "occurredAt": "2026-05-04T10:00:00Z",
  "correlationId": "corr_001",
  "aggregateType": "transaction",
  "aggregateId": "txn_001",
  "payload": {
    "transactionId": "txn_001",
    "senderId": "user_a",
    "receiverId": "user_b",
    "amount": 5000000,
    "currency": "VND",
    "idempotencyKey": "client-request-001",
    "deviceFingerprint": "fp_abc123",
    "ipAddress": "118.69.1.1"
  }
}
```

### fraud.passed

```json
{
  "eventId": "evt_002",
  "eventType": "fraud.passed",
  "occurredAt": "2026-05-04T10:00:01Z",
  "correlationId": "corr_001",
  "aggregateType": "transaction",
  "aggregateId": "txn_001",
  "payload": {
    "transactionId": "txn_001",
    "riskScore": 20,
    "decision": "APPROVE",
    "reasons": []
  }
}
```

### fraud.rejected

```json
{
  "eventId": "evt_003",
  "eventType": "fraud.rejected",
  "occurredAt": "2026-05-04T10:00:01Z",
  "correlationId": "corr_001",
  "aggregateType": "transaction",
  "aggregateId": "txn_002",
  "payload": {
    "transactionId": "txn_002",
    "riskScore": 100,
    "decision": "DECLINE",
    "reasons": [
      {
        "ruleCode": "RECEIVER_BLACKLISTED",
        "score": 100,
        "evidence": "receiver user_x is active in blacklist"
      }
    ]
  }
}
```

### ledger.recorded

```json
{
  "eventId": "evt_010",
  "eventType": "ledger.recorded",
  "occurredAt": "2026-05-04T10:00:05Z",
  "correlationId": "corr_001",
  "aggregateType": "transaction",
  "aggregateId": "txn_001",
  "payload": {
    "transactionId": "txn_001",
    "entries": [
      {
        "walletId": "wallet_sender",
        "entryType": "DEBIT",
        "amount": 5000000,
        "currency": "VND"
      },
      {
        "walletId": "wallet_receiver",
        "entryType": "CREDIT",
        "amount": 5000000,
        "currency": "VND"
      }
    ]
  }
}
```

## 6. API tối thiểu

### Auth

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/auth/register` | Đăng ký |
| POST | `/auth/login` | Đăng nhập |

### User

| Method | Endpoint | Mục đích |
|---|---|---|
| GET | `/users/me` | Lấy profile |
| PATCH | `/users/{id}/verify` | Admin verify KYC |

### Wallet

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/wallets/deposit` | Deposit demo |
| GET | `/wallets/me` | Xem ví |
| GET | `/wallets/me/transactions` | Lịch sử ví |

### Transaction

| Method | Endpoint | Mục đích |
|---|---|---|
| POST | `/transfers` | Tạo transfer |
| GET | `/transfers` | List transfer |
| GET | `/transfers/{id}` | Transfer detail |
| POST | `/transfers/{id}/confirm-otp` | Confirm OTP optional |

### Fraud

| Method | Endpoint | Mục đích |
|---|---|---|
| GET | `/fraud/checks` | Xem fraud checks |
| GET | `/fraud/checks/{transactionId}` | Fraud detail |
| PATCH | `/fraud/blacklist/{userId}` | Blacklist user |

### Ledger

| Method | Endpoint | Mục đích |
|---|---|---|
| GET | `/ledger/entries` | Query ledger |
| GET | `/ledger/entries/{transactionId}` | Ledger theo transaction |

### Notification

| Method | Endpoint | Mục đích |
|---|---|---|
| GET | `/notifications` | List notification |
| WS | `/ws` | WebSocket realtime |

## 7. Error response chuẩn

API nên dùng RFC 7807 Problem Details để UI và client xử lý lỗi nhất quán.

### Format

```json
{
  "type": "https://docs.example.com/errors/FRAUD_001_BLACKLISTED_RECEIVER",
  "title": "Transfer rejected by fraud rules",
  "status": 422,
  "detail": "Receiver is blacklisted",
  "instance": "/transfers",
  "errorCode": "FRAUD_001_BLACKLISTED_RECEIVER",
  "correlationId": "corr_001",
  "timestamp": "2026-05-04T10:00:00Z"
}
```

### Error code gợi ý

| HTTP | errorCode | Khi nào dùng |
|---:|---|---|
| 400 | `REQ_001_VALIDATION_FAILED` | Request thiếu field hoặc sai format |
| 401 | `AUTH_001_UNAUTHORIZED` | Thiếu/sai token |
| 403 | `AUTH_002_FORBIDDEN` | Không đủ quyền |
| 409 | `IDEMP_001_KEY_BODY_MISMATCH` | Cùng idempotency key nhưng body khác |
| 409 | `WALLET_002_CONCURRENT_UPDATE` | Wallet bị update đồng thời, client có thể retry |
| 422 | `WALLET_001_INSUFFICIENT_FUNDS` | Không đủ số dư |
| 422 | `FRAUD_001_BLACKLISTED_RECEIVER` | Receiver blacklist |
| 422 | `FRAUD_002_KYC_NOT_VERIFIED` | Sender chưa KYC verified |
| 423 | `WALLET_003_WALLET_FROZEN` | Wallet bị khóa |
| 500 | `SYS_001_INTERNAL_ERROR` | Lỗi hệ thống |

## 8. Request/response transfer

### Request

```http
POST /transfers
Authorization: Bearer <token>
Idempotency-Key: 9e7b2c7e-1234-4567
Content-Type: application/json
```

```json
{
  "receiverId": "user_b",
  "amount": 5000000,
  "currency": "VND",
  "description": "Pay invoice",
  "device": {
    "fingerprint": "fp_abc123",
    "type": "WEB",
    "os": "Windows",
    "browser": "Chrome"
  }
}
```

### Response

```json
{
  "transactionId": "txn_001",
  "status": "PENDING",
  "message": "Transfer request accepted and is being processed"
}
```

## 9. Saga recovery

Transaction Service đóng vai trò Saga Orchestrator nên cần cơ chế recovery khi service crash giữa luồng xử lý.

### Rule recovery

- Background job chạy định kỳ, ví dụ mỗi 1 phút.
- Quét transaction ở trạng thái `RISK_CHECKING`, `PROCESSING`, `COMPENSATING`, `CHALLENGE_REQUIRED`, `HELD_FOR_REVIEW` quá timeout.
- Nếu transaction đang đợi event nhưng chưa nhận được sau ngưỡng cấu hình, đánh dấu `PENDING_REVIEW` hoặc publish lại command idempotent.
- Mọi command publish lại phải có `business_key` ổn định để consumer không double-apply.
- Nếu compensation fail nhiều lần, tạo notification cho admin/analyst.

### Timeout gợi ý

| State | Timeout demo | Hành động |
|---|---:|---|
| `RISK_CHECKING` | 2 phút | Publish lại `transaction.created` hoặc mark `PENDING_REVIEW` |
| `PROCESSING` | 5 phút | Kiểm tra saga step, publish lại command idempotent |
| `COMPENSATING` | 5 phút | Retry compensation, sau max retry thì `PENDING_REVIEW` |
| `CHALLENGE_REQUIRED` | 5 phút | Expire OTP, mark `REJECTED` |
| `HELD_FOR_REVIEW` | 24 giờ demo tùy chọn | Escalate hoặc notify analyst |

## 10. Test case tối thiểu

| Nhóm         | Test case                                            |
| ------------ | ---------------------------------------------------- |
| Idempotency  | Cùng key cùng body trả response cũ                   |
| Idempotency  | Cùng key khác body trả lỗi                           |
| Fraud        | Amount threshold tạo score đúng                      |
| Fraud        | Receiver blacklist bị reject                         |
| Wallet       | Không cho balance âm                                 |
| Wallet       | Reserve làm giảm available balance                   |
| Wallet       | Hai debit đồng thời không làm balance âm             |
| Ledger       | Completed transfer có đúng 1 debit và 1 credit       |
| Ledger       | Tổng debit bằng tổng credit                          |
| Ledger       | Publish lại ledger command không tạo posting trùng   |
| Saga         | Fraud reject không gọi wallet                        |
| Saga         | Credit fail thì compensate debit                     |
| Saga         | Transaction kẹt PROCESSING quá timeout được recovery |
| Notification | Transaction completed push WebSocket event           |
|              |                                                      |
