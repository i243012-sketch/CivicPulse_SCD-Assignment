/**
 * API client for CivicPulse backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export interface Complaint {
  id: string;
  text: string;
  location: string;
  reporter_contact: string | null;
  category: string;
  priority: string;
  status: string;
  ai_summary: string | null;
  triaged_by: string;
  triage_latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface ComplaintCreate {
  text: string;
  location: string;
  reporter_contact?: string;
}

export interface ComplaintListResponse {
  items: Complaint[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Stats {
  by_category: Array<{ category: string; count: number }>;
  by_priority: Array<{ priority: string; count: number }>;
  total_complaints: number;
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }
  return response.json();
}

export const api = {
  async createComplaint(data: ComplaintCreate): Promise<Complaint> {
    const response = await fetch(`${API_BASE_URL}/complaints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Complaint>(response);
  },

  async getComplaint(id: string): Promise<Complaint> {
    const response = await fetch(`${API_BASE_URL}/complaints/${id}`);
    return handleResponse<Complaint>(response);
  },

  async listComplaints(params: {
    category?: string;
    priority?: string;
    status?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<ComplaintListResponse> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, String(value));
      }
    });
    const response = await fetch(
      `${API_BASE_URL}/complaints?${searchParams}`
    );
    return handleResponse<ComplaintListResponse>(response);
  },

  async updateComplaintStatus(
    id: string,
    status: string
  ): Promise<Complaint> {
    const response = await fetch(`${API_BASE_URL}/complaints/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    return handleResponse<Complaint>(response);
  },

  async getStats(): Promise<Stats> {
    const response = await fetch(`${API_BASE_URL}/stats`);
    return handleResponse<Stats>(response);
  },
};

export { ApiError };
