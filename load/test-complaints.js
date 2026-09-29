/**
 * k6 Load Test for CivicPulse Complaints API
 * 
 * This test simulates realistic user behavior against the complaints endpoints
 * to validate system performance and HPA (Horizontal Pod Autoscaler) behavior.
 * 
 * Run with:
 *   k6 run load/test-complaints.js
 * 
 * Monitor HPA during test:
 *   kubectl get hpa -n civicpulse-prod -w
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users over 2 minutes
    { duration: '5m', target: 50 },   // Stay at 50 users for 5 minutes
    { duration: '2m', target: 100 },  // Ramp up to 100 users over 2 minutes
    { duration: '5m', target: 100 },  // Stay at 100 users for 5 minutes (triggers HPA)
    { duration: '2m', target: 50 },   // Ramp down to 50 users over 2 minutes
    { duration: '3m', target: 0 },    // Ramp down to 0 users (watch HPA scale down)
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests should complete within 500ms
    http_req_failed: ['rate<0.1'],     // Error rate should be less than 10%
    errors: ['rate<0.1'],
  },
};

// Configuration - adjust based on your environment
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const API_BASE = `${BASE_URL}/api`;

// Sample complaint data for POST requests
const SAMPLE_COMPLAINTS = [
  {
    title: 'Pothole on Main Street',
    description: 'Large pothole causing traffic issues near intersection',
    category: 'infrastructure',
    location: '123 Main St',
  },
  {
    title: 'Broken streetlight',
    description: 'Streetlight not working for past week',
    category: 'utilities',
    location: '456 Oak Ave',
  },
  {
    title: 'Garbage not collected',
    description: 'Missed garbage pickup for two weeks',
    category: 'sanitation',
    location: '789 Elm Dr',
  },
  {
    title: 'Park maintenance needed',
    description: 'Playground equipment needs repair',
    category: 'parks',
    location: '321 Park Blvd',
  },
  {
    title: 'Noise complaint',
    description: 'Construction noise at night',
    category: 'noise',
    location: '654 Quiet Lane',
  },
];

function getRandomComplaint() {
  return SAMPLE_COMPLAINTS[Math.floor(Math.random() * SAMPLE_COMPLAINTS.length)];
}

export default function () {
  // Scenario 1: Health check (10% of requests)
  if (Math.random() < 0.1) {
    const healthRes = http.get(`${API_BASE}/meta/health`);
    check(healthRes, {
      'health check status is 200': (r) => r.status === 200,
    }) || errorRate.add(1);
    sleep(1);
    return;
  }

  // Scenario 2: Get all complaints (30% of requests)
  if (Math.random() < 0.3) {
    const params = {
      headers: { 'Content-Type': 'application/json' },
    };
    const listRes = http.get(`${API_BASE}/complaints?limit=20`, params);
    check(listRes, {
      'list complaints status is 200': (r) => r.status === 200,
      'list response has data': (r) => JSON.parse(r.body).length >= 0,
    }) || errorRate.add(1);
    sleep(1);
    return;
  }

  // Scenario 3: Get stats (20% of requests - tests Redis caching)
  if (Math.random() < 0.2) {
    const statsRes = http.get(`${API_BASE}/stats`);
    check(statsRes, {
      'stats status is 200': (r) => r.status === 200,
      'stats has category_breakdown': (r) => {
        const body = JSON.parse(r.body);
        return body.category_breakdown !== undefined;
      },
    }) || errorRate.add(1);
    sleep(0.5);
    return;
  }

  // Scenario 4: Create new complaint (40% of requests - main load generator)
  const complaint = getRandomComplaint();
  const payload = JSON.stringify(complaint);
  const params = {
    headers: { 'Content-Type': 'application/json' },
  };

  const createRes = http.post(`${API_BASE}/complaints`, payload, params);
  const success = check(createRes, {
    'create complaint status is 201': (r) => r.status === 201,
    'create response has id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.id !== undefined;
      } catch (e) {
        return false;
      }
    },
    'create response has priority': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.priority !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  if (!success) {
    errorRate.add(1);
  }

  // If complaint was created successfully, try to fetch it
  if (createRes.status === 201) {
    try {
      const createdComplaint = JSON.parse(createRes.body);
      const getRes = http.get(`${API_BASE}/complaints/${createdComplaint.id}`);
      check(getRes, {
        'get complaint by id status is 200': (r) => r.status === 200,
      }) || errorRate.add(1);
    } catch (e) {
      // Ignore parsing errors for this optional step
    }
  }

  sleep(1);
}

/**
 * Expected HPA Behavior:
 * 
 * 1. Initial state: 2 replicas (as configured in k8s/overlays/prod/backend-hpa.yaml)
 * 2. During 50 VUs stage: Should remain at 2 replicas (below threshold)
 * 3. During 100 VUs stage: Should scale up to 3-5 replicas (CPU/memory pressure)
 * 4. During ramp-down: Should gradually scale back to 2 replicas (minReplicas)
 * 
 * To observe:
 *   # In one terminal, run k6
 *   k6 run load/test-complaints.js
 * 
 *   # In another terminal, watch HPA
 *   kubectl get hpa -n civicpulse-prod -w
 * 
 *   # Also watch pod count
 *   kubectl get pods -n civicpulse-prod -l app=backend -w
 * 
 * For screenshots, capture:
 *   1. HPA at start (2 replicas)
 *   2. HPA during peak load (scaled up)
 *   3. HPA after cooldown (back to 2 replicas)
 */
