# 06. Load testing plan

## 1. Mục tiêu

Load testing dùng để chứng minh transfer flow chịu được tải đồng thời và các cơ chế an toàn tiền tệ hoạt động đúng:

- Optimistic locking không để wallet âm.
- Idempotency không tạo duplicate transaction.
- Fraud velocity rule vẫn hoạt động khi request tăng cao.
- Kafka consumer không bị lag quá mức.
- API latency/error rate nằm trong ngưỡng demo chấp nhận được.

## 2. Công cụ

Khuyến nghị cho MVP:

- `k6`: nhẹ, viết script bằng JavaScript, dễ chạy trong CI.
- `JMeter`: phù hợp nếu muốn UI test plan truyền thống.

Mặc định nên dùng `k6` vì dễ demo và dễ đưa vào GitHub Actions.

## 3. Target API

Endpoint chính:

```http
POST /transfers
Authorization: Bearer <token>
Idempotency-Key: <unique-key>
Content-Type: application/json
```

Các endpoint phụ:

- `POST /auth/login`
- `GET /transfers/{id}`
- `GET /wallets/me`
- `GET /ledger/entries/{transactionId}`

## 4. Load scenarios

| Scenario | Mục tiêu | Tải gợi ý |
|---|---|---:|
| Baseline transfer | Đo latency bình thường | 50 RPS trong 5 phút |
| Concurrent debit same wallet | Kiểm tra optimistic locking | 200-500 RPS vào cùng sender |
| Idempotency retry storm | Kiểm tra duplicate request | 100 RPS dùng lặp lại một phần idempotency key |
| Fraud velocity spike | Trigger rule nhiều giao dịch trong 5 phút | 500 RPS trong 2-5 phút |
| Stress test | Tìm điểm nghẽn demo | 500-1000 RPS nếu máy local chịu được |

## 5. Metrics cần đo

### API metrics

- Request rate.
- p50/p95/p99 latency.
- Error rate.
- HTTP status distribution.
- `REQ_001_VALIDATION_FAILED`, `WALLET_001_INSUFFICIENT_FUNDS`, `WALLET_002_CONCURRENT_UPDATE`, `IDEMP_001_KEY_BODY_MISMATCH`.

### Business correctness metrics

- Không có wallet balance âm.
- Số transaction created không vượt quá số idempotency key unique.
- Mỗi completed transaction có đúng một ledger posting settlement.
- Tổng debit bằng tổng credit.
- Fraud rule velocity được kích hoạt khi đủ ngưỡng.

### Infrastructure metrics

- Kafka consumer lag.
- PostgreSQL connection pool usage.
- Redis latency.
- CPU/memory của transaction-service, wallet-service, fraud-service.
- Zipkin trace latency theo service.

## 6. Acceptance criteria cho demo

| Tiêu chí | Target demo |
|---|---:|
| Transfer API p95 latency baseline | < 500ms |
| Error rate baseline | < 1% |
| Negative wallet balance | 0 case |
| Duplicate transaction do retry | 0 case |
| Ledger imbalance | 0 case |
| Kafka consumer lag sau spike | Tự giảm về gần 0 sau vài phút |

## 7. k6 script outline

```javascript
import http from 'k6/http';
import { check } from 'k6';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

export const options = {
  stages: [
    { duration: '1m', target: 50 },
    { duration: '3m', target: 200 },
    { duration: '1m', target: 0 },
  ],
};

export default function () {
  const idempotencyKey = uuidv4();
  const payload = JSON.stringify({
    receiverId: 'user_b',
    amount: 10000,
    currency: 'VND',
    description: 'load test transfer',
    device: {
      fingerprint: `k6-${__VU}`,
      type: 'WEB',
      os: 'Linux',
      browser: 'k6'
    }
  });

  const res = http.post('http://localhost:8080/transfers', payload, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${__ENV.ACCESS_TOKEN}`,
      'Idempotency-Key': idempotencyKey,
    },
  });

  check(res, {
    'status is 202 or business error': (r) => [202, 409, 422].includes(r.status),
  });
}
```

## 8. Post-test verification queries

Sau load test, cần chạy verification:

```text
1. Query wallet không có available_balance < 0.
2. Query idempotency key không tạo nhiều hơn 1 transaction.
3. Query completed transaction nào thiếu ledger DEBIT/CREDIT.
4. Query transaction PROCESSING quá timeout.
5. Query Kafka lag đã giảm sau khi ngừng test.
```

Load test không chỉ để khoe throughput; mục tiêu chính là chứng minh correctness khi hệ thống bị concurrency pressure.

