/**
 * api/client.js
 * ─────────────
 * Axios instance pre-configured for the Breathe ESG API.
 *
 * Features:
 *  • Reads base URL from VITE_API_URL env var (defaults to /api)
 *  • Request interceptor injects JWT Bearer token from localStorage
 *  • Response interceptor catches 401s and redirects to /login
 *  • Convenience wrappers for every API endpoint the frontend needs
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

const client = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

/* ── Request interceptor: attach JWT ──────────────────────── */
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/* ── Response interceptor: handle 401 ─────────────────────── */
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear stale tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      // Only redirect if we're not already on the login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

/* ── Auth endpoints ───────────────────────────────────────── */
export const authAPI = {
  login: (email, password) =>
    client.post('/auth/login/', { email, password }),
  refreshToken: (refresh) =>
    client.post('/auth/refresh/', { refresh }),
  me: () => client.get('/auth/me/'),
};

/* ── Dashboard endpoints ──────────────────────────────────── */
export const dashboardAPI = {
  getStats: () => client.get('/dashboard/stats/'),
};

/* ── Upload / Ingestion endpoints ─────────────────────────── */
export const uploadAPI = {
  uploadFile: (formData, onUploadProgress) =>
    client.post('/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    }),
  getBatchStatus: (batchId) =>
    client.get(`/batches/${batchId}/`),
  getDataSources: () => client.get('/data-sources/'),
};

/* ── Normalized records endpoints ─────────────────────────── */
export const recordsAPI = {
  list: (params) => client.get('/records/', { params }),
  get: (id) => client.get(`/records/${id}/`),
  update: (id, data) => client.patch(`/records/${id}/`, data),
  approve: (id, comment) =>
    client.post(`/records/${id}/approve/`, { comment }),
  reject: (id, comment) =>
    client.post(`/records/${id}/reject/`, { comment }),
  lock: (id) => client.post(`/records/${id}/lock/`),
  bulkApprove: (ids) =>
    client.post('/records/bulk-approve/', { ids }),
  bulkReject: (ids, comment) =>
    client.post('/records/bulk-reject/', { ids, comment }),
};

/* ── Audit trail endpoints ────────────────────────────────── */
export const auditAPI = {
  list: (params) => client.get('/audit-logs/', { params }),
  getForRecord: (recordId) =>
    client.get(`/records/${recordId}/audit-trail/`),
};

export default client;
