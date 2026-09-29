/**
 * Simplified k6 Load Test for Local Docker Compose
 * 
 * This is a shorter version for demonstration purposes.
 * For actual HPA testing, run the full test-complaints.js against K8s cluster.
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 20 },   // Ramp up to 20 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.1'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const API_BASE = `${BASE_URL}/api`;

const SAMPLE_COMPLAINTS = [
  {
    title: 'Pothole on Main Street',
    description: 'Large pothole causing traffic issues',
    category: 'infrastructure',
    location: '123 Main St',
  },
  {
    title: 'Broken streetlight',
    description: 'Streetlight not working',
    category: 'utilities',
    location: '456 Oak Ave',
  },
];

function getRandomComplaint() {
  return SAMPLE_COMPLAINTS[Math.floor(Math.random() * SAMPLE_COMPLAINTS.length)];
}

export default function () {
  // 60% - Create complaint
  if (Math.random() < 0.6) {
    const complaint = getRandomComplaint();
    const payload = JSON.stringify(complaint);
    const params = { headers: { 'Content-Type': 'application/json' } };
    
    const res = http.post(`${API_BASE}/complaints`, payload, params);
    check(res, {
      'create status 201': (r) => r.status === 201,
      'has id': (r) => JSON.parse(r.body).id !== undefined,
    }) || errorRate.add(1);
  }
  
  // 30% - List complaints
  else if (Math.random() < 0.3) {
    const res = http.get(`${API_BASE}/complaints?limit=10`);
    check(res, {
      'list status 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  }
  
  // 10% - Get stats
  else {
    const res = http.get(`${API_BASE}/stats`);
    check(res, {
      'stats status 200': (r) => r.status === 200,
    }) || errorRate.add(1);
  }
  
  sleep(1);
}
