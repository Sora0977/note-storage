# 02. Data flow

## 1. Context data flow

```mermaid
flowchart TD
    Customer[Customer Web UI] --> Gateway[API Gateway]
    Admin[Admin/Risk Dashboard] --> Gateway

    Gateway --> Auth[Auth Service]
    Gateway --> UserSvc[User Service]
    Gateway --> TxSvc[Transaction Service]
    Gateway --> WalletSvc[Wallet Service]
    Gateway --> FraudSvc[Fraud Service]
    Gateway --> LedgerSvc[Ledger Service]

    TxSvc --> TxDB[(Transaction DB)]
    UserSvc --> UserDB[(User DB)]
    WalletSvc --> WalletDB[(Wallet DB)]
    FraudSvc --> FraudDB[(Fraud DB)]
    LedgerSvc --> LedgerDB[(Ledger DB)]

    TxSvc --> Kafka[(Kafka)]
    FraudSvc --> Kafka
    WalletSvc --> Kafka
    LedgerSvc --> Kafka
    Kafka --> NotifySvc[Notification Service]
    NotifySvc --> NotiDB[(Notification DB)]
    NotifySvc --> Customer
    NotifySvc --> Admin

    FraudSvc --> Redis[(Redis Feature Store)]
    Gateway --> Zipkin[Zipkin/Tracing]
    TxSvc --> Zipkin
    FraudSvc --> Zipkin
    WalletSvc --> Zipkin
```

## 2. Event-driven transfer data flow

```mermaid
flowchart LR
    A[POST /transfers] --> B[Validate request]
    B --> C[Check Idempotency-Key]
    C --> D[(transactions)]
    C --> E[(idempotency_keys)]
    D --> F[(outbox_events)]
    F --> G[Outbox Publisher]
    G --> T1[Kafka: transaction.created]

    T1 --> H[Fraud Service]
    H --> I[(fraud_checks)]
    H --> R[(Redis velocity keys)]
    H --> T2[Kafka: fraud.passed/rejected/challenge/hold]

    T2 --> J[Transaction Saga]
    J --> T3[Kafka: wallet commands]
    T3 --> K[Wallet Service]
    K --> L[(wallets)]
    K --> M[(wallet_holds)]
    K --> T4[Kafka: wallet events]

    T4 --> J
    J --> T5[Kafka: ledger.record.command]
    T5 --> N[Ledger Service]
    N --> O[(ledger_entries)]
    N --> T6[Kafka: ledger.recorded]

    T6 --> J
    J --> P[(transaction_status_history)]
    J --> T7[Kafka: transaction.completed/failed]
    T7 --> Q[Notification Service]
    Q --> S[WebSocket /ws]
    S --> U[React Dashboard]
```

## 3. Risk feature data flow

```mermaid
flowchart TD
    TxCreated[transaction.created event] --> FeatureBuilder[Feature Builder]

    FeatureBuilder --> UserProfile[(User/Profile DB)]
    FeatureBuilder --> TxHistory[(Transaction History)]
    FeatureBuilder --> Redis[(Redis)]
    FeatureBuilder --> Blacklist[(Blacklist Table)]

    Redis --> V1[velocity:user:{id}:5m]
    Redis --> V2[amount:user:{id}:10m]
    Redis --> V3[receiver:user:{id}:10m]
    Redis --> V4[device:{fingerprint}]

    FeatureBuilder --> Features[Feature Set]
    Features --> RuleEngine[Rule Engine]
    RuleEngine --> Rules[(Active Fraud Rules)]
    RuleEngine --> Score[Risk Score]
    Score --> DecisionPolicy[Decision Policy]
    DecisionPolicy --> RiskDecision[(fraud_checks/risk_decisions)]
    RiskDecision --> Kafka[Kafka: risk decision event]
```

## 4. Realtime dashboard data flow

```mermaid
flowchart LR
    Kafka[(Kafka)] --> N[Notification Service]
    N --> NDB[(notifications)]
    N --> WS[WebSocket STOMP /ws]
    WS --> UI[React Dashboard]

    UI --> API[REST API]
    API --> Tx[Transaction Service]
    API --> Wallet[Wallet Service]
    API --> Fraud[Fraud Service]
    API --> Ledger[Ledger Service]

    Tx --> TxDB[(transactions)]
    Wallet --> WalletDB[(wallets)]
    Fraud --> FraudDB[(fraud_checks)]
    Ledger --> LedgerDB[(ledger_entries)]

    UI --> Views[Transaction List, Detail, Risk Alerts, Wallet Balance]
```

## 5. Data flow theo trạng thái transaction

| Bước | Input | Service xử lý | Output |
|---:|---|---|---|
| 1 | Transfer request | API Gateway | Request đã auth, correlation id |
| 2 | Request + Idempotency-Key | Transaction Service | Transaction `PENDING`, outbox event |
| 3 | `transaction.created` | Fraud Service | Risk score, decision, reason |
| 4 | `fraud.passed` | Transaction Service | Status `APPROVED/PROCESSING` |
| 5 | Wallet command | Wallet Service | Reserve/debit/credit event |
| 6 | Wallet success | Ledger Service | Debit/credit ledger entries |
| 7 | `ledger.recorded` | Transaction Service | Status `COMPLETED` |
| 8 | Status event | Notification Service | WebSocket alert/dashboard update |

## 6. Data ownership

| Data | Owner service | Ghi bởi | Đọc bởi |
|---|---|---|---|
| User profile/KYC | user-service | user-service/admin | transaction, fraud |
| Wallet balance | wallet-service | wallet-service | wallet API, dashboard |
| Transaction status | transaction-service | transaction-service | dashboard, notification |
| Idempotency key | transaction-service | transaction-service | transaction-service |
| Fraud check/decision | fraud-service | fraud-service | dashboard, transaction |
| Ledger entry | ledger-service | ledger-service | auditor, dashboard |
| Notification | notification-service | notification-service | dashboard/user |
| Audit log | audit/transaction-service | nhiều service | auditor/admin |

## 7. Reliability data flow

```mermaid
flowchart TD
    LocalTx[Local DB Transaction] --> BusinessData[(Business Table)]
    LocalTx --> Outbox[(outbox_events)]
    Outbox --> Publisher[Outbox Publisher]
    Publisher --> Kafka[(Kafka)]
    Kafka --> Consumer[Consumer Service]
    Consumer --> Inbox[(processed_messages)]
    Inbox --> Decision{Message seen?}
    Decision -->|Yes| Skip[Skip duplicate]
    Decision -->|No| Process[Process business action]
    Process --> ConsumerDB[(Consumer DB)]
```

Ý nghĩa:

- Outbox giúp tránh lỗi lưu DB thành công nhưng publish Kafka thất bại.
- Inbox/processed_messages giúp tránh Kafka message bị xử lý lặp.
- Idempotency key giúp tránh API retry tạo duplicate transaction.

## 8. Saga recovery data flow

```mermaid
flowchart TD
    Scheduler[Scheduled Saga Recovery Job] --> Query[(transactions)]
    Query --> Stuck{Stuck state?}
    Stuck -->|No| Done[Skip]
    Stuck -->|RISK_CHECKING timeout| RiskRetry[Republish transaction.created with same business_key]
    Stuck -->|PROCESSING timeout| StepCheck[Check saga_step]
    Stuck -->|COMPENSATING timeout| CompRetry[Retry compensation command]
    Stuck -->|CHALLENGE_REQUIRED timeout| ExpireOtp[Expire OTP and mark REJECTED]

    StepCheck --> WalletRetry[Republish idempotent wallet/ledger command]
    RiskRetry --> Kafka[(Kafka)]
    WalletRetry --> Kafka
    CompRetry --> Kafka
    ExpireOtp --> TxDB[(Transaction DB)]

    Kafka --> Consumers[Idempotent Consumers]
    Consumers --> Inbox[(processed_messages/business_key)]
```

Rule:

- Recovery job không được tạo business operation mới.
- Mọi retry phải dùng cùng `business_key` để consumer bỏ qua nếu đã xử lý.
- Nếu retry vượt quá max attempt, transaction chuyển `PENDING_REVIEW` và notification được gửi cho admin/analyst.
