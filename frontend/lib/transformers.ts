// frontend/lib/transformers.ts
import { PerformanceMetric, PeerAccount, Insight } from '@/types/dashboard';

// Transform backend data to dashboard format
// Transform backend data to dashboard format
export function transformBackendAnalysis(backendData: any) {
  // Log the structure for debugging
  console.log('Backend data structure:', {
    hasInsights: !!backendData.insights,
    insightsType: Array.isArray(backendData.insights) ? 'array' : typeof backendData.insights,
    insightsKeys: backendData.insights ? Object.keys(backendData.insights) : []
  });
  
  return {
    id: backendData.analysis_id || backendData.id,
    created_at: backendData.created_at,
    x_score: calculateXScore(backendData),
    score_change: backendData.score_change || 0,
    percentile: backendData.percentile || 0,
    credits_used: backendData.credits_used || 15,
    performance_metrics: transformPerformanceMetrics(backendData),
    top_peers: transformPeers(backendData.peer_profiles || backendData.peers || []),
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
  const peers = data.peer_profiles || data.peers || [];
  
  // Calculate peer averages
  let peerAvgEngagement = 0;
  let peerAvgGrowth = 0;
  let peerAvgPosts = 0;
  
  if (peers.length > 0) {
    peerAvgEngagement = peers.reduce((sum: number, p: any) => {
      const grok = p.grok_profile || {};
      const followers = p.basic_metrics?.followers_count || 1;
      const likes = grok.average_likes_per_post || 0;
      return sum + (likes / followers * 100);
    }, 0) / peers.length;
    
    peerAvgGrowth = peers.reduce((sum: number, p: any) => {
      const grok = p.grok_profile || {};
      return sum + (grok.estimated_monthly_follower_growth_percent || 0);
    }, 0) / peers.length;
    
    peerAvgPosts = peers.reduce((sum: number, p: any) => {
      const grok = p.grok_profile || {};
      return sum + (grok.posting_frequency_per_week || 0);
    }, 0) / peers.length;
  }
  
  // Fallback to API provided averages if no peers
  const apiPeerAvg = data.peer_averages || {};
  
  const userEngagement = (profile.avg_engagement_rate || 0) * 100;
  const peerEngagement = peerAvgEngagement || (apiPeerAvg.avg_engagement_rate || 0) * 100;
  
  return [
    {
      metric: 'Engagement',
      you: Math.round(userEngagement),
      peers: Math.round(peerEngagement),
      fullMark: 100,
    },
    {
      metric: 'Growth',
      you: Math.min(Math.round(profile.growth_30d || 0), 100),
      peers: Math.min(Math.round(peerAvgGrowth || apiPeerAvg.growth_30d || 0), 100),
      fullMark: 100,
    },
    {
      metric: 'Consistency',
      you: Math.min(Math.round((profile.posting_frequency_per_week || 0) * 7), 100),
      peers: Math.min(Math.round((peerAvgPosts || apiPeerAvg.posting_frequency_per_week || 0) * 7), 100),
      fullMark: 100,
    },
    {
      metric: 'Virality',
      you: Math.round(profile.viral_index || 65),
      peers: Math.round(apiPeerAvg.viral_index || 78),
      fullMark: 100,
    },
    {
      metric: 'Content Quality',
      you: Math.round(profile.content_quality_score || 75),
      peers: Math.round(apiPeerAvg.content_quality_score || 80),
      fullMark: 100,
    },
    {
      metric: 'Niche Authority',
      you: Math.round(profile.niche_authority_score || 70),
      peers: Math.round(apiPeerAvg.niche_authority_score || 80),
      fullMark: 100,
    },
  ];
}

// Transform peers data
function transformPeers(peers: any[]): PeerAccount[] {
  return peers.slice(0, 4).map((peer, index) => {
    const grok = peer.grok_profile || {};
    const basic = peer.basic_metrics || {};
    
    return {
      id: peer.id || `peer-${index}`,
      name: peer.name || peer.handle?.replace('@', '') || 'Unknown',
      handle: peer.handle || '@unknown',
      avatar: getInitials(peer.name || peer.handle || 'U'),
      avatar_url: peer.profile_image || peer.profile_image_url || null,
      score: Math.round(peer.match_score || grok.estimated_monthly_follower_growth_percent || 85),
      trend: `+${(grok.estimated_monthly_follower_growth_percent || (Math.random() * 10 + 2)).toFixed(1)}%`,
      followers_count: basic.followers_count || 0,
      growth_rate: grok.estimated_monthly_follower_growth_percent || 0,
      peer_insights: peer.peer_insights || undefined,  // ADD THIS LINE
    };
  });
}

// Transform insights from Grok
function transformInsights(insights: any): Insight[] {
  // Handle case where insights might not be an array
  if (!insights) {
    return [];
  }
  
  // If insights is an object with nested structure, extract the insights array
  if (typeof insights === 'object' && !Array.isArray(insights)) {
    // Check if there's an 'insights' property
    if (Array.isArray(insights.insights)) {
      insights = insights.insights;
    } else {
      // If it's a nested object structure, try to extract insights from categories
      const extractedInsights: any[] = [];
      const categories = ['posting_pattern', 'content_type', 'topic_strategy', 'structure_formatting'];
      
      for (const category of categories) {
        if (insights[category] && Array.isArray(insights[category].insights)) {
          extractedInsights.push(...insights[category].insights);
        }
      }
      
      if (extractedInsights.length > 0) {
        insights = extractedInsights;
      } else {
        return [];
      }
    }
  }

    // Now insights should be an array
    if (!Array.isArray(insights)) {
      console.error('Insights is not an array:', insights);
      return [];
    }
    
    // Transform the insights array
    return insights.slice(0, 3).map((insight, index) => ({
      title: insight.title || insight.category || `Insight ${index + 1}`,
      finding: insight.finding || insight.observation || insight.current_state || '',
      impact: insight.impact || insight.gap_impact || insight.expected_result || 'Significant growth potential',
      action: insight.action || insight.recommendation || '',
      priority: insight.priority === 'critical' ? 1 : insight.priority === 'high' ? 2 : insight.priority === 'medium' ? 3 : (index + 1),
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