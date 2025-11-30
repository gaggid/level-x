// frontend/types/dashboard.ts
export interface UserData {
  id: string;
  handle: string;
  display_name: string;
  avatar_url?: string;
  followers_count: number;
  following_count: number;
  credits: number;
}

export interface PerformanceMetric {
  metric: string;
  you: number;
  peers: number;
  fullMark: number;
}

export interface PeerAccount {
  id: string;
  name: string;
  handle: string;
  avatar: string;
  score: number;
  trend: string;
  followers_count: number;
  growth_rate: number;
}

export interface Insight {
  title: string;
  finding: string;
  impact: string;
  action: string;
  priority: number;
}

export interface AnalysisResult {
  id: string;
  created_at: string;
  x_score: number;
  score_change: number;
  percentile: number;
  credits_used: number;
  performance_metrics: PerformanceMetric[];
  top_peers: PeerAccount[];
  insights: Insight[];
}

export interface AnalysisHistoryItem {
  id: string;
  created_at: string;
  x_score: number;
  credits_used: number;
}