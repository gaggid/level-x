// User Types
export interface User {
  id: string;
  x_handle: string;
  x_user_id: string;
  x_name: string;
  x_profile_image: string;
  followers_count: number;
  subscription_tier: "free" | "pro";
  credits: number;
  created_at: string;
}

// Profile Types
export interface UserProfile {
  handle: string;
  user_id: string;
  name: string;
  bio: string;
  profile_image: string;
  basic_metrics: BasicMetrics;
  grok_profile: GrokProfile;
  niche: string;
  content_style: Record<string, any>;
  posting_rhythm: PostingRhythm;
  engagement_baseline: EngagementBaseline;
  growth_velocity: GrowthVelocity;
}

export interface BasicMetrics {
  followers_count: number;
  following_count: number;
  tweet_count: number;
  listed_count: number;
  follower_following_ratio: number;
}

export interface GrokProfile {
  handle: string;
  followers: number;
  primary_niche: string;
  secondary_topics: string[];
  content_style: string;
  average_likes_per_post: number;
  average_views_per_post: number;
  growth_trend_last_30_days: string;
  estimated_monthly_follower_growth_percent: number;
  posting_frequency_per_week: number;
  visual_content_ratio: string;
  language_mix: string;
  key_hashtags: string[];
  strengths: string[];
  weaknesses_for_growth: string[];
}

export interface PostingRhythm {
  posts_per_week: number;
  consistency_score: number;
  date_range_days: number;
  total_analyzed: number;
}

export interface EngagementBaseline {
  avg_likes: number;
  avg_retweets: number;
  avg_replies: number;
  engagement_rate: number;
  total_engagements: number;
  engagement_per_tweet: number;
}

export interface GrowthVelocity {
  estimated_30d_growth: number;
  growth_rate_pct: number;
}

// Peer Types
export interface PeerProfile extends UserProfile {
  match_score: number;
  match_reason: string;
  growth_edge: string;
  growth_advantage: string;
}

// Analysis Types
export interface Analysis {
  growth_score: number;
  growth_score_explanation: string;
  posting_analysis: PostingAnalysis;
  content_analysis: ContentAnalysis;
  topic_analysis: TopicAnalysis;
  structure_analysis: StructureAnalysis;
  insights: Insight[];
  quick_wins: string[];
  peer_standout_tactics: string[];
}

export interface PostingAnalysis {
  user_pattern: {
    posts_per_week: number;
    consistency: string;
    description: string;
  };
  peer_pattern: {
    posts_per_week: number;
    consistency: string;
    description: string;
  };
  gap: string;
  impact: string;
}

export interface ContentAnalysis {
  user_style: {
    thread_usage: string;
    media_usage: string;
    link_frequency: string;
    tweet_length: string;
    unique_traits: string[];
  };
  peer_style: {
    thread_usage: string;
    media_usage: string;
    link_frequency: string;
    tweet_length: string;
    unique_traits: string[];
  };
  gap: string;
  impact: string;
}

export interface TopicAnalysis {
  user_distribution: {
    primary_focus: string;
    secondary_topics: string;
    trending_participation: string;
  };
  peer_distribution: {
    primary_focus: string;
    secondary_topics: string;
    trending_participation: string;
  };
  gap: string;
  impact: string;
}

export interface StructureAnalysis {
  user_formatting: {
    emoji_usage: string;
    hashtag_strategy: string;
    thread_hooks: string;
    cta_presence: string;
  };
  peer_formatting: {
    emoji_usage: string;
    hashtag_strategy: string;
    thread_hooks: string;
    cta_presence: string;
  };
  gap: string;
  impact: string;
}

export interface Insight {
  title: string;
  category: string;
  priority: "critical" | "high" | "medium" | "low";
  current_state: string;
  peer_state: string;
  gap_impact: string;
  action: string;
  expected_result: string;
  measurement: string;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface AnalysisResult {
  user_profile: UserProfile;
  peers: PeerProfile[];
  analysis: Analysis;
  analysis_id: string;
  created_at: string;
}