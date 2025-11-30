// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('user_token');
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {  // ← Fixed: added opening (
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.clear();
      window.location.href = '/';
    }
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  async getCurrentUser() {
    return fetchAPI('/api/user/me');
  },

  async getLatestAnalysis() {
    try {
      return await fetchAPI('/api/analysis/latest');
    } catch (error: any) {
      if (error.message.includes('404')) return null;
      throw error;
    }
  },

  async runAnalysis(analysisType: 'basic' | 'standard' | 'deep' = 'standard') {
    return fetchAPI('/api/analysis/run', {
      method: 'POST',
      body: JSON.stringify({ type: analysisType }),
    });
  },

  async getAnalysisHistory(limit: number = 5) {
    return fetchAPI(`/api/analysis/history?limit=${limit}`);
  },

  async getAnalysisById(analysisId: string) {
    return fetchAPI(`/api/analysis/${analysisId}`);
  },

  async getCredits() {
    return fetchAPI('/api/user/credits');
  },
};