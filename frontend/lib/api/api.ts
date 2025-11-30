// frontend/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// For now, let's use mock data until we connect the real backend
const USE_MOCK_DATA = false; // Set to false when backend is ready

// Mock data generator
function generateMockData() {
  return {
    user: {
      id: '1',
      handle: '@your_handle',
      display_name: 'Your Name',
      followers_count: 5234,
      following_count: 892,
      credits: 250,
    },
    latestAnalysis: {
      id: '1',
      analyzed_at: new Date().toISOString(),
      user_profile: {
        avg_engagement_rate: 0.045,
        growth_30d: 8.5,
        posting_frequency_per_week: 12,
        viral_index: 65,
        content_quality_score: 80,
        niche_authority_score: 70,
        posting_consistency: 0.85,
      },
      peer_averages: {
        avg_engagement_rate: 0.052,
        growth_30d: 12.3,
        posting_frequency_per_week: 15,
        viral_index: 78,
        content_quality_score: 75,
        niche_authority_score: 80,
      },
      peers: [
        {
          id: '1',
          name: 'Elena Martinez',
          handle: '@elena_ai',
          match_score: 98,
          growth_rate: 12.5,
          followers_count: 5800,
        },
        {
          id: '2',
          name: 'Marcus Davidson',
          handle: '@dev_marc',
          match_score: 92,
          growth_rate: 8.2,
          followers_count: 5400,
        },
        {
          id: '3',
          name: 'Sarah Smith',
          handle: '@sarah_ship',
          match_score: 88,
          growth_rate: 5.7,
          followers_count: 5100,
        },
        {
          id: '4',
          name: 'Davide Olsen',
          handle: '@design_d',
          match_score: 85,
          growth_rate: 3.2,
          followers_count: 4900,
        },
      ],
      insights: [
        {
          title: 'Post More Threads on Weekends',
          finding: 'Your top peers post 3x more thread-style content on Saturdays and Sundays, averaging 4.2 threads per weekend.',
          impact: 'Potential +45% engagement increase',
          action: 'Schedule 2 educational threads for this Saturday morning (8-10 AM) focusing on your core niche topics. Use numbered formats (1/7, 2/7) to encourage full thread reads.',
          priority: 1,
        },
        {
          title: 'Add More Visual Content',
          finding: 'Peers with 85+ scores include images/videos in 78% of posts vs your 42%. Visual tweets get 2.3x more engagement.',
          impact: 'Estimated +65% reach boost',
          action: 'Create 5 branded quote graphics this week using Canva. Post one daily at 2 PM. Include your handle watermark for virality tracking.',
          priority: 2,
        },
        {
          title: 'Engage More in Comments',
          finding: 'High-growth accounts reply to 15+ comments per day within first 2 hours of posting. You average 3 replies per post.',
          impact: 'Algorithm boost + community building',
          action: 'Set a 30-minute timer after each post to engage with every comment. Ask follow-up questions to spark conversations.',
          priority: 3,
        },
      ],
      score_change: 2.4,
      percentile: 68,
      credits_used: 15,
    },
    history: [
      { id: '1', created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), x_score: 84.5, credits_used: 15 },
      { id: '2', created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), x_score: 82.1, credits_used: 15 },
      { id: '3', created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(), x_score: 80.3, credits_used: 15 },
    ],
  };
}

// Helper function for API calls
async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('user_token');
  
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
    if (USE_MOCK_DATA) {
      return new Promise(resolve => setTimeout(() => resolve(generateMockData().user), 500));
    }
    return fetchAPI('/api/user/me');
  },

  // Get user's latest analysis
  async getLatestAnalysis() {
    if (USE_MOCK_DATA) {
      return new Promise(resolve => setTimeout(() => resolve(generateMockData().latestAnalysis), 800));
    }
    return fetchAPI('/api/analysis/latest');
  },

  // Run new analysis
  async runAnalysis(analysisType: 'basic' | 'standard' | 'deep' = 'standard') {
    if (USE_MOCK_DATA) {
      return new Promise(resolve => 
        setTimeout(() => resolve(generateMockData().latestAnalysis), 3000)
      );
    }
    return fetchAPI('/api/analysis/run', {
      method: 'POST',
      body: JSON.stringify({ type: analysisType }),
    });
  },

  // Get user's analysis history
  async getAnalysisHistory(limit: number = 5) {
    if (USE_MOCK_DATA) {
      return new Promise(resolve => setTimeout(() => resolve(generateMockData().history), 600));
    }
    return fetchAPI(`/api/analysis/history?limit=${limit}`);
  },

  // Get specific analysis by ID
  async getAnalysisById(analysisId: string) {
    if (USE_MOCK_DATA) {
      return new Promise(resolve => setTimeout(() => resolve(generateMockData().latestAnalysis), 500));
    }
    return fetchAPI(`/api/analysis/${analysisId}`);
  },

  // Get user credits
  async getCredits() {
    if (USE_MOCK_DATA) {
      return new Promise(resolve => setTimeout(() => resolve({ credits: 250 }), 400));
    }
    return fetchAPI('/api/user/credits');
  },
};