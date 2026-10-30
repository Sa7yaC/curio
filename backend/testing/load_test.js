import http from 'k6/http';
import { check, sleep } from 'k6';

// Resolves base URL and ensures /api prefix matches Django routing (path('api/', include('store.urls')))
const RAW_BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const BASE_URL = RAW_BASE_URL.endsWith('/api')
  ? RAW_BASE_URL
  : `${RAW_BASE_URL.replace(/\/+$/, '')}/api`;

const USERNAME = __ENV.K6_USERNAME || '';
const PASSWORD = __ENV.K6_PASSWORD || '';
const TENANT_ID = Number(__ENV.K6_TENANT_ID || 1);

export const options = {
  scenarios: {
    api_load: {
      executor: 'ramping-vus',
      startVUs: 0,

      stages: [
        { duration: '30s', target: 25 },
        { duration: '60s', target: 50 },
        { duration: '60s', target: 100 },
        { duration: '60s', target: 150 },
        { duration: '60s', target: 200 },
        { duration: '30s', target: 0 },
      ],

      gracefulRampDown: '30s',
    },
  },

  thresholds: {
    checks: ['rate>0.95'],
    http_req_failed: ['rate<0.05'],
    http_req_duration: [
      'p(95)<2000',
      'p(99)<5000',
    ],
  },
};


// --------------------------------------------------
// Helper: Headers
// --------------------------------------------------

function getHeaders(token = '') {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
}


// --------------------------------------------------
// Main Load Test
// --------------------------------------------------

export default function () {

  // ------------------------------------------------
  // 1. REGISTER
  // ------------------------------------------------

  const uniqueId = `${Date.now()}_${__VU}_${__ITER}_${Math.floor(Math.random() * 100000)}`;
  const username = `k6_user_${uniqueId}`;
  const email = `${username}@example.com`;

  const registerPayload = JSON.stringify({
    username: username,
    email: email,
    password: 'K6TestPassword123!',
    password2: 'K6TestPassword123!',
    first_name: 'K6',
    last_name: 'LoadTest',
    phone: '9999999999',
    address: 'Load Test Address',
    role: 'customer',
    tenant_id: TENANT_ID,
  });

  const registerResponse = http.post(
    `${BASE_URL}/auth/register/`,
    registerPayload,
    {
      headers: getHeaders(),
    }
  );

  check(registerResponse, {
    'registration: status is 2xx': (response) =>
      response.status >= 200 && response.status < 300,
  });


  // ------------------------------------------------
  // 2. LOGIN
  // ------------------------------------------------

  let token = '';

  // Use provided credentials, or authenticate with the user just registered above
  const loginUsername = USERNAME || username;
  const loginPassword = PASSWORD || 'K6TestPassword123!';

  const loginPayload = JSON.stringify({
    username: loginUsername,
    password: loginPassword,
  });

  const loginResponse = http.post(
    `${BASE_URL}/auth/login/`,
    loginPayload,
    {
      headers: getHeaders(),
    }
  );

  check(loginResponse, {
    'login: status is 200': (response) =>
      response.status === 200,
  });

  if (loginResponse.status === 200) {
    try {
      const body = loginResponse.json();

      token =
        body.access ||
        body.access_token ||
        '';

    } catch (error) {
      token = '';
    }
  }


  // ------------------------------------------------
  // 3. GET PRODUCTS
  // ------------------------------------------------

  const productsResponse = http.get(
    `${BASE_URL}/products/`,
    {
      headers: getHeaders(token),
    }
  );

  check(productsResponse, {
    'products: status is 200': (response) =>
      response.status === 200,
  });


  // ------------------------------------------------
  // 4. GET MY ORDERS
  // ------------------------------------------------

  const myOrdersResponse = http.get(
    `${BASE_URL}/orders/my_orders/`,
    {
      headers: getHeaders(token),
    }
  );

  check(myOrdersResponse, {
    'my orders: status is 200': (response) =>
      response.status === 200,
  });


  // ------------------------------------------------
  // 5. GET ORDERS
  // ------------------------------------------------

  const ordersResponse = http.get(
    `${BASE_URL}/orders/`,
    {
      headers: getHeaders(token),
    }
  );

  check(ordersResponse, {
    'orders: valid response': (response) =>
      response.status === 200 ||
      response.status === 403,
  });


  // Small delay between iterations
  sleep(1);
}
