# 01. Sequence diagrams

## 1. Happy path - transfer hoàn thành

```mermaid
sequenceDiagram
    autonumber
    actor User as User A
    participant UI as React Dashboard
    participant GW as API Gateway
    participant Tx as Transaction Service / Saga Orchestrator
    participant TxDB as Transaction DB
    participant Kafka as Kafka
    participant Fraud as Fraud Service
    participant Wallet as Wallet Service
    participant Ledger as Ledger Service
    participant Notify as Notification Service

    User->>UI: Submit transfer to User B
    UI->>GW: POST /transfers + JWT + Idempotency-Key
    GW->>Tx: Forward request
    Tx->>Tx: Validate sender, receiver, amount
    Tx->>TxDB: Check idempotency key
    Tx->>TxDB: Save transaction PENDING + outbox event
    Tx-->>UI: 202 Accepted, transactionId
    Tx->>Kafka: Publish transaction.created

    Kafka-->>Fraud: Consume transaction.created
    Fraud->>Fraud: Build features and run rules
    Fraud->>Kafka: Publish fraud.passed

    Kafka-->>Tx: Consume fraud.passed
    Tx->>TxDB: Mark APPROVED/PROCESSING
    Tx->>Kafka: Publish wallet.reserve.command

    Kafka-->>Wallet: Reserve funds
    Wallet->>Wallet: Check available balance
    Wallet->>Kafka: Publish wallet.reserved

    Kafka-->>Tx: Consume wallet.reserved
    Tx->>Kafka: Publish wallet.debit.command
    Kafka-->>Wallet: Debit sender
    Wallet->>Kafka: Publish wallet.debited

    Kafka-->>Tx: Consume wallet.debited
    Tx->>Kafka: Publish wallet.credit.command
    Kafka-->>Wallet: Credit receiver
    Wallet->>Kafka: Publish wallet.credited

    Kafka-->>Tx: Consume wallet.credited
    Tx->>Kafka: Publish ledger.record.command
    Kafka-->>Ledger: Write double-entry ledger
    Ledger->>Ledger: Create DEBIT and CREDIT entries
    Ledger->>Kafka: Publish ledger.recorded

    Kafka-->>Tx: Consume ledger.recorded
    Tx->>TxDB: Mark COMPLETED
    Tx->>Kafka: Publish transaction.completed
    Kafka-->>Notify: Consume transaction.completed
    Notify-->>UI: WebSocket transaction completed
```

## 2. Fraud reject path

```mermaid
sequenceDiagram
    autonumber
    actor User as User A
    participant UI as React Dashboard
    participant GW as API Gateway
    participant Tx as Transaction Service
    participant Kafka as Kafka
    participant Fraud as Fraud Service
    participant Notify as Notification Service

    User->>UI: Submit high-risk transfer
    UI->>GW: POST /transfers + Idempotency-Key
    GW->>Tx: Forward request
    Tx->>Tx: Save transaction PENDING
    Tx->>Kafka: Publish transaction.created
    Tx-->>UI: 202 Accepted

    Kafka-->>Fraud: Consume transaction.created
    Fraud->>Fraud: Hit critical rules
    Fraud->>Fraud: score >= 80 or blacklist hit
    Fraud->>Kafka: Publish fraud.rejected

    Kafka-->>Tx: Consume fraud.rejected
    Tx->>Tx: Mark REJECTED with reason
    Tx->>Kafka: Publish transaction.rejected
    Kafka-->>Notify: Consume transaction.rejected
    Notify-->>UI: WebSocket fraud alert + rejected status
```

## 3. Medium risk - OTP challenge

```mermaid
sequenceDiagram
    autonumber
    actor User as User A
    participant UI as React Dashboard
    participant Tx as Transaction Service
    participant Kafka as Kafka
    participant Fraud as Fraud Service
    participant OTP as OTP/Notification Service
    participant Wallet as Wallet Service
    participant Ledger as Ledger Service

    UI->>Tx: POST /transfers
    Tx->>Kafka: Publish transaction.created
    Kafka-->>Fraud: Consume transaction.created
    Fraud->>Fraud: score between 30 and 59
    Fraud->>Kafka: Publish risk.challenge_required

    Kafka-->>Tx: Consume risk.challenge_required
    Tx->>Tx: Mark CHALLENGE_REQUIRED
    Tx->>Kafka: Publish otp.challenge.create
    Kafka-->>OTP: Create OTP
    OTP-->>UI: WebSocket/notification OTP sent

    User->>UI: Enter OTP
    UI->>Tx: POST /transfers/{id}/confirm-otp
    Tx->>OTP: Verify OTP

    alt OTP valid
        OTP-->>Tx: challenge.passed
        Tx->>Tx: Mark APPROVED/PROCESSING
        Tx->>Wallet: Continue reserve/debit/credit
        Wallet->>Ledger: Trigger ledger record
        Ledger-->>Tx: ledger.recorded
        Tx-->>UI: COMPLETED
    else OTP invalid or expired
        OTP-->>Tx: challenge.failed
        Tx->>Tx: Mark REJECTED
        Tx-->>UI: REJECTED
    end
```

## 4. High risk - manual review hold

```mermaid
sequenceDiagram
    autonumber
    actor User as User A
    actor Analyst as Risk Analyst
    participant UI as React Dashboard
    participant Tx as Transaction Service
    participant Kafka as Kafka
    participant Fraud as Fraud Service
    participant Case as Case Management
    participant Audit as Audit Log

    UI->>Tx: POST /transfers
    Tx->>Kafka: Publish transaction.created
    Kafka-->>Fraud: Consume transaction.created
    Fraud->>Fraud: score between 60 and 79
    Fraud->>Kafka: Publish risk.hold_required

    Kafka-->>Tx: Consume risk.hold_required
    Tx->>Tx: Mark HELD_FOR_REVIEW
    Tx->>Kafka: Publish risk.case.create
    Kafka-->>Case: Create case with evidence
    Case-->>Analyst: Case appears in dashboard

    Analyst->>Case: Review evidence and approve/reject
    Case->>Audit: Save analyst decision

    alt Analyst approves
        Case->>Kafka: Publish case.approved
        Kafka-->>Tx: Mark APPROVED/PROCESSING
    else Analyst rejects
        Case->>Kafka: Publish case.rejected
        Kafka-->>Tx: Mark REJECTED
    end
```

## 5. Idempotency retry

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as React Dashboard
    participant Tx as Transaction Service
    participant DB as Transaction DB

    User->>UI: Click submit transfer
    UI->>Tx: POST /transfers Idempotency-Key=K1 Body=A
    Tx->>DB: No existing key K1
    Tx->>DB: Save idempotency K1 + request_hash(A)
    Tx->>DB: Save transaction TX001
    Tx-->>UI: 202 Accepted TX001

    Note over UI,Tx: Client times out and retries

    UI->>Tx: POST /transfers Idempotency-Key=K1 Body=A
    Tx->>DB: Find key K1
    Tx->>DB: request_hash matches
    Tx-->>UI: Return cached response TX001

    UI->>Tx: POST /transfers Idempotency-Key=K1 Body=B
    Tx->>DB: Find key K1
    Tx->>DB: request_hash differs
    Tx-->>UI: 409 Conflict
```

## 6. Compensation khi credit hoặc ledger fail

```mermaid
sequenceDiagram
    autonumber
    participant Tx as Transaction Service / Saga Orchestrator
    participant Kafka as Kafka
    participant Wallet as Wallet Service
    participant Ledger as Ledger Service
    participant Notify as Notification Service

    Tx->>Kafka: wallet.debit.command
    Kafka-->>Wallet: Debit sender
    Wallet->>Kafka: wallet.debited
    Kafka-->>Tx: wallet.debited

    Tx->>Kafka: wallet.credit.command
    Kafka-->>Wallet: Credit receiver

    alt Credit receiver fails
        Wallet->>Kafka: wallet.credit_failed
        Kafka-->>Tx: wallet.credit_failed
        Tx->>Kafka: wallet.compensate_debit.command
        Kafka-->>Wallet: Refund sender / release funds
        Wallet->>Kafka: wallet.compensated
        Kafka-->>Tx: wallet.compensated
        Tx->>Tx: Mark FAILED with reason
        Tx->>Kafka: transaction.failed
        Kafka-->>Notify: Push failed notification
    else Credit succeeds but ledger fails
        Wallet->>Kafka: wallet.credited
        Kafka-->>Tx: wallet.credited
        Tx->>Kafka: ledger.record.command
        Kafka-->>Ledger: Write ledger
        Ledger->>Kafka: ledger.record_failed
        Kafka-->>Tx: ledger.record_failed
        Tx->>Kafka: wallet.reverse_transfer.command
        Kafka-->>Wallet: Reverse sender/receiver balances
        Wallet->>Kafka: wallet.compensated
        Kafka-->>Tx: wallet.compensated
        Tx->>Tx: Mark PENDING_REVIEW or FAILED
    end
```
