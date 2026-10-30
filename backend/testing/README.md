# Load Testing with k6

This directory contains load testing scripts for the multi-tenant ecommerce platform API using [k6](https://k6.io/).

## Files

- `load_test.js`: Main k6 load test script testing authentication (`/register/`, `/login/`), product listing (`/products/`), and order history (`/orders/my_orders/`, `/orders/`).

---

## Prerequisites

1. Ensure [k6](https://k6.io/docs/get-started/installation/) is installed.
   Verify installation:
   ```bash
   k6 version
   ```

2. Ensure the Django backend server is running:
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `BASE_URL` | Base URL of the API. Supports both root (`http://127.0.0.1:8000`) and API root (`http://127.0.0.1:8000/api`) | `http://127.0.0.1:8000` |
| `K6_USERNAME` | (Optional) Username for an existing account to test login & authenticated endpoints | `""` |
| `K6_PASSWORD` | (Optional) Password for the above user account | `""` |
| `K6_TENANT_ID` | (Optional) Tenant ID for the generated users during registration | `1` |

---

## Running the Load Test

### 1. Default Run (Registration & Public/Anonymous endpoints)
```bash
k6 run testing/load_test.js
```

### 2. With Authenticated User Credentials
```bash
k6 run -e BASE_URL=http://127.0.0.1:8000 -e K6_USERNAME=testuser -e K6_PASSWORD=password123 testing/load_test.js
```

### 3. Quick Smoke Test / Dry Run (1 VU, 5 seconds)
To verify endpoints and script syntax quickly before running full load:
```bash
k6 run --vus 1 --duration 5s testing/load_test.js
```

---

## Test Scenario & Ramp-up Profile

The test executes a **ramping-vus** scenario over **4.5 minutes** reaching up to **200 concurrent Virtual Users**:

| Stage | Duration | Target VUs |
|---|---|---|
| 1 | 30s | 25 VUs |
| 2 | 60s | 50 VUs |
| 3 | 60s | 100 VUs |
| 4 | 60s | 150 VUs |
| 5 | 60s | 200 VUs |
| 6 | 30s | Ramp down to 0 |

### Thresholds (Pass / Fail Criteria)
- **Checks Success Rate**: > 95% (`checks: ['rate>0.95']`)
- **HTTP Failure Rate**: < 5% (`http_req_failed: ['rate<0.05']`)
- **95th percentile Response Duration**: < 2000 ms (`p(95)<2000`)
- **99th percentile Response Duration**: < 5000 ms (`p(99)<5000`)
