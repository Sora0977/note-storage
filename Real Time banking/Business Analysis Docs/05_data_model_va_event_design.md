# 05. Data model và event design

## 1. Service responsibilities

| Service | Trách nhiệm |
|---|---|
| api-gateway | Routing, JWT validation, CORS, rate limit, correlation id |
| auth-service | Register, login, password hash, JWT, role |
| user-service | User profile, KYC status, admin verify user |
| wallet-service | Wallet, deposit, reserve, release, debit, credit, balance view |
| transaction-service | Transfer API, idempotency, transaction state machine, Saga orchestration |
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
- consumer_name
- processed_at
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

wallet_holds
- id
- transaction_id
- wallet_id
- amount
- status: HELD, RELEASED, CAPTURED
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
- created_at

blacklist_accounts
- id
- user_id
- reason
- active
- created_at

processed_messages
- id
- message_id
- consumer_name
- processed_at
```

### ledger-service

```text
ledger_entries
- id
- transaction_id
- wallet_id/account_id
- entry_type: DEBIT, CREDIT, REVERSAL_DEBIT, REVERSAL_CREDIT
- amount
- currency
- created_at

processed_messages
- id
- message_id
- consumer_name
- processed_at
```

Rule bắt buộc:

```text
sum(DEBIT) = sum(CREDIT) for each completed transaction
```

Ledger không update/xóa entry cũ. Nếu cần sửa sai, tạo reversal entry.

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

## 7. Request/response transfer

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

## 8. Test case tối thiểu

| Nhóm | Test case |
|---|---|
| Idempotency | Cùng key cùng body trả response cũ |
| Idempotency | Cùng key khác body trả lỗi |
| Fraud | Amount threshold tạo score đúng |
| Fraud | Receiver blacklist bị reject |
| Wallet | Không cho balance âm |
| Wallet | Reserve làm giảm available balance |
| Ledger | Completed transfer có đúng 1 debit và 1 credit |
| Ledger | Tổng debit bằng tổng credit |
| Saga | Fraud reject không gọi wallet |
| Saga | Credit fail thì compensate debit |
| Notification | Transaction completed push WebSocket event |

