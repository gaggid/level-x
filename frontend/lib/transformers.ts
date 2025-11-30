// frontend/lib/transformers.ts
import { PerformanceMetric, PeerAccount, Insight } from '@/types/dashboard';

// Transform backend data to dashboard format
export function transformBackendAnalysis(backendData: any) {
  return {
    id: backendData.id,
    created_at: backendData.analyzed_at || backendData.created_at,
    x_score: calculateXScore(backendData),
    score_change: backendData.score_change || 0,
    percentile: backendData.percentile || 0,
    credits_used: backendData.credits_used || 15,
    performance_metrics: transformPerformanceMetrics(backendData),
    top_peers: transformPeers(backendData.peers || []),
    insights: transformInsights(backendData.insights || []),
  };
}

// Calculate X-Score from backend metrics
function calculateXScore(data: any): number {
  const profile = data.user_profile || {};
  const engagement = profile.avg_engagement_rate || 0;
  const growth = profile.growth_30d || 0;
  const consistency = profile.posting_consistency || 0;
  
  const score = (
    engagement * 100 * 0.3 +
    growth * 0.4 +
    consistency * 100 * 0.3
  );
  
  return Math.min(Math.round(score * 10) / 10, 100);
}

// Transform to radar chart format
function transformPerformanceMetrics(data: any): PerformanceMetric[] {
  const profile = data.user_profile || {};
  const peerAvg = data.peer_averages || {};

  return [
    {
      metric: 'Engagement',
      you: Math.round((profile.avg_engagement_rate || 0) * 100),
      peers: Math.round((peerAvg.avg_engagement_rate || 0) * 100),
      fullMark: 100,
    },
    {
      metric: 'Growth',
      you: Math.min(Math.round(profile.growth_30d || 0), 100),
      peers: Math.min(Math.round(peerAvg.growth_30d || 0), 100),
      fullMark: 100,
    },
    {
      metric: 'Consistency',
      you: Math.min(Math.round((profile.posting_frequency_per_week || 0) * 7), 100),
      peers: Math.min(Math.round((peerAvg.posting_frequency_per_week || 0) * 7), 100),
      fullMark: 100,
    },
    {
      metric: 'Virality',
      you: Math.round(profile.viral_index || 65),
      peers: Math.round(peerAvg.viral_index || 78),
      fullMark: 100,
    },
    {
      metric: 'Content Quality',
      you: Math.round(profile.content_quality_score || 75),
      peers: Math.round(peerAvg.content_quality_score || 80),
      fullMark: 100,
    },
    {
      metric: 'Niche Authority',
      you: Math.round(profile.niche_authority_score || 70),
      peers: Math.round(peerAvg.niche_authority_score || 80),
      fullMark: 100,
    },
  ];
}

// Transform peers data
function transformPeers(peers: any[]): PeerAccount[] {
  return peers.slice(0, 4).map((peer, index) => ({
    id: peer.id || `peer-${index}`,
    name: peer.name || peer.handle?.replace('@', '') || 'Unknown',
    handle: peer.handle || '@unknown',
    avatar: getInitials(peer.name || peer.handle || 'U'),
    score: Math.round(peer.match_score || peer.score || 85),
    trend: `+${(peer.growth_rate || (Math.random() * 10 + 2)).toFixed(1)}%`,
    followers_count: peer.followers_count || 0,
    growth_rate: peer.growth_rate || 0,
  }));
}

// Transform insights from Grok
function transformInsights(insights: any[]): Insight[] {
  return insights.slice(0, 3).map((insight, index) => ({
    title: insight.title || insight.category || `Insight ${index + 1}`,
    finding: insight.finding || insight.observation || '',
    impact: insight.impact || insight.expected_impact || 'Significant growth potential',
    action: insight.action || insight.recommendation || '',
    priority: insight.priority || index + 1,
  }));
}

// Helper: Get initials from name
function getInitials(name: string): string {
  return name
    .replace('@', '')
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

// Format date
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor(diffMs / (1000 * 60));

  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return `${Math.floor(diffDays / 30)} months ago`;
}

// Full date format for tooltips
export function formatFullDate(dateString: string): string {
  return new Date(dateString).toLocaleString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}