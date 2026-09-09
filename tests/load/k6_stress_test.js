// =====================================================================
// DentalCare Pro - k6 Enterprise Load & Stress Testing Suite
// Simulates 10,000 Concurrent Virtual Users (VUs) across SaaS Workflows
// =====================================================================

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom Metrics
const ApiLatency = new Trend('dentalcare_api_latency_ms');
const OdontogramLatency = new Trend('dentalcare_odontogram_latency_ms');
const BillingLatency = new Trend('dentalcare_billing_latency_ms');
const AuthLatency = new Trend('dentalcare_auth_latency_ms');
const ErrorRate = new Rate('dentalcare_error_rate');
const CompletedWorkflows = new Counter('dentalcare_completed_workflows');

// Configuration & Ramping Profile
export const options = {
  stages: [
    { duration: '1m', target: 1000 },   // Warm-up ramp to 1,000 VUs
    { duration: '3m', target: 5000 },   // Scale to normal peak (5,000 VUs)
    { duration: '5m', target: 10000 },  // Stress peak (10,000 VUs)
    { duration: '2m', target: 10000 },  // Sustained enterprise peak load
    { duration: '2m', target: 2000 },   // Step-down recovery
    { duration: '1m', target: 0 },      // Ramp down to 0
  ],
  thresholds: {
    // Enterprise SLA Requirements
    'http_req_duration': ['p(95)<200', 'p(99)<400'], // 95% of requests under 200ms
    'dentalcare_api_latency_ms': ['p(95)<200'],
    'dentalcare_odontogram_latency_ms': ['p(95)<250'],
    'dentalcare_auth_latency_ms': ['p(95)<150'],
    'dentalcare_error_rate': ['rate<0.01'],            // Error rate < 1%
    'http_req_failed': ['rate<0.01'],
  },
};

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';

const HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-Clinic-ID': 'clinic_1001',
  'X-Branch-ID': 'branch_central',
};

export default function () {
  const userTypeRoll = Math.random();

  // Workflow 1: Authentication & Token Verification (10% traffic)
  if (userTypeRoll < 0.10) {
    group('01_Auth_Flow', function () {
      const payload = JSON.stringify({
        username: `staff_user_${__VU}@dentalcare.internal`,
        password: 'SecureTestPassword123!',
      });
      const start = new Date();
      const res = http.post(`${BASE_URL}/api/v1/auth/login`, payload, { headers: HEADERS });
      AuthLatency.add(new Date() - start);

      const passed = check(res, {
        'status is 200 or 401': (r) => r.status === 200 || r.status === 401,
      });
      ErrorRate.add(!passed);
      CompletedWorkflows.add(1);
    });
  }

  // Workflow 2: Receptionist Patient & Appointment Flow (40% traffic)
  else if (userTypeRoll < 0.50) {
    group('02_Patient_Appointment_Flow', function () {
      const patientId = `pat_${(__VU % 500) + 1}`;
      
      // Patient Search
      const searchRes = http.get(`${BASE_URL}/api/v1/patients?query=John&limit=10`, { headers: HEADERS });
      ApiLatency.add(searchRes.timings.duration);
      check(searchRes, { 'patients returned': (r) => r.status === 200 || r.status === 404 });

      // Daily Calendar View
      const apptRes = http.get(`${BASE_URL}/api/v1/appointments?date=2026-09-09`, { headers: HEADERS });
      ApiLatency.add(apptRes.timings.duration);
      check(apptRes, { 'appointments list ok': (r) => r.status === 200 });

      CompletedWorkflows.add(1);
    });
  }

  // Workflow 3: Dentist Odontogram & Treatment Flow (25% traffic)
  else if (userTypeRoll < 0.75) {
    group('03_Odontogram_Clinical_Flow', function () {
      const patientId = `pat_${(__VU % 200) + 1}`;
      
      // Fetch 32-Tooth Interactive Odontogram
      const start = new Date();
      const odoRes = http.get(`${BASE_URL}/api/v1/patients/${patientId}/odontogram`, { headers: HEADERS });
      OdontogramLatency.add(new Date() - start);
      check(odoRes, { 'odontogram retrieved': (r) => r.status === 200 || r.status === 404 });

      // Record Surface Finding (Tooth #14 MOD Caries)
      const findingPayload = JSON.stringify({
        tooth_number: 14,
        surface: 'MOD',
        condition_code: 'CARIES',
        severity: 'MODERATE',
        notes: 'Simulated high-load clinical entry',
      });
      const postRes = http.post(
        `${BASE_URL}/api/v1/patients/${patientId}/odontogram/findings`,
        findingPayload,
        { headers: HEADERS }
      );
      OdontogramLatency.add(postRes.timings.duration);
      check(postRes, { 'finding recorded': (r) => r.status === 200 || r.status === 201 || r.status === 404 });

      CompletedWorkflows.add(1);
    });
  }

  // Workflow 4: Billing, Payments & Invoicing (15% traffic)
  else if (userTypeRoll < 0.90) {
    group('04_Billing_Invoicing_Flow', function () {
      const invoiceId = `inv_${(__VU % 100) + 1}`;
      
      const invRes = http.get(`${BASE_URL}/api/v1/billing/invoices/${invoiceId}`, { headers: HEADERS });
      BillingLatency.add(invRes.timings.duration);
      check(invRes, { 'invoice status valid': (r) => r.status === 200 || r.status === 404 });

      CompletedWorkflows.add(1);
    });
  }

  // Workflow 5: Executive Analytics & Telemetry (10% traffic)
  else {
    group('05_Executive_Metrics_Flow', function () {
      const metricsRes = http.get(`${BASE_URL}/metrics`, { headers: HEADERS });
      ApiLatency.add(metricsRes.timings.duration);
      check(metricsRes, { 'metrics scrape 200': (r) => r.status === 200 });

      CompletedWorkflows.add(1);
    });
  }

  sleep(Math.random() * 2 + 1); // Realistic user think-time between 1s and 3s
}
