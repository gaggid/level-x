// frontend/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper function for API calls
async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('user_token');
  
  // FIX: Correct template literal syntax
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}

// API Methods
export const api = {
  // Get current user info
  async getCurrentUser() {
    return fetchAPI('/api/user/me');
  },

  // Get user's latest analysis
  async getLatestAnalysis() {
    return fetchAPI('/api/analysis/latest');
  },

  // Run new analysis
  async runAnalysis(analysisType: 'basic' | 'standard' | 'deep' = 'standard') {
    return fetchAPI('/api/analysis/run', {
      method: 'POST',
      body: JSON.stringify({ type: analysisType }),
    });
  },

  // Get user's analysis history
  async getAnalysisHistory(limit: number = 5) {
    return fetchAPI(`/api/analysis/history?limit=${limit}`);
  },

  // Get specific analysis by ID
  async getAnalysisById(analysisId: string) {
    return fetchAPI(`/api/analysis/${analysisId}`);
  },

  // Get user credits
  async getCredits() {
    return fetchAPI('/api/user/credits');
  },
};