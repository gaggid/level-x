# ai/insights_generator.py
from typing import Dict, List, Optional
from ai.grok_client import GrokClient, GrokAPIError
import json
import logging

logger = logging.getLogger(__name__)


class InsightsGenerator:
    """
    Deep X/Twitter growth analysis using Grok AI
    Compares user profile with high-performing peers to identify growth opportunities
    """
    
    def __init__(self, cost_tracker=None):
        self.grok = GrokClient()
        self.cost_tracker = cost_tracker
        logger.info("InsightsGenerator initialized with LevelX AI")
    
    def generate_insights(
        self,
        user_profile: Dict,
        peer_profiles: List[Dict],
        num_insights: int = 3
    ) -> Dict:
        """
        Generate comprehensive growth insights by comparing user with peers
        
        Args:
            user_profile: Full user profile dict (with grok_profile)
            peer_profiles: List of peer profile dicts (with grok_profile)
            num_insights: Number of actionable insights to generate (default 3)
        
        Returns:
            Dict containing:
            - growth_score: 0-10 score comparing user to peers
            - insights: List of actionable insights
            - comparison_data: Detailed metrics comparison
            - posting_analysis: Deep posting pattern analysis
            - content_analysis: Content structure and style analysis
            - topic_analysis: Niche and topic distribution analysis
        """
        logger.info(f"Generating comprehensive insights for @{user_profile['handle']}")
        
        try:
            # Build comprehensive analysis prompt
            analysis_data = self._generate_deep_analysis(
                user_profile,
                peer_profiles,
                num_insights
            )
            
            logger.info(f"✅ Generated {len(analysis_data.get('insights', []))} insights")
            return analysis_data
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            raise
    
    def _generate_deep_analysis(
        self,
        user_profile: Dict,
        peer_profiles: List[Dict],
        num_insights: int
    ) -> Dict:
        """
        Use Grok to perform deep comparative analysis
        """
        # Extract profile data
        user_grok = user_profile.get('grok_profile', {})
        user_handle = user_profile.get('handle', 'unknown')
        user_followers = user_profile.get('basic_metrics', {}).get('followers_count', 0)
        
        # Build peer summary
        peer_summaries = []
        for peer in peer_profiles[:5]:
            peer_grok = peer.get('grok_profile', {})
            peer_summaries.append({
                'handle': peer.get('handle', ''),
                'followers': peer.get('basic_metrics', {}).get('followers_count', 0),
                'niche': peer_grok.get('primary_niche', ''),
                'topics': peer_grok.get('secondary_topics', []),
                'style': peer_grok.get('content_style', ''),
                'posts_per_week': peer_grok.get('posting_frequency_per_week', 0),
                'likes_per_post': peer_grok.get('average_likes_per_post', 0),
                'views_per_post': peer_grok.get('average_views_per_post', 0),
                'growth_rate': peer_grok.get('estimated_monthly_follower_growth_percent', 0),
                'visual_ratio': peer_grok.get('visual_content_ratio', 'medium'),
                'hashtags': peer_grok.get('key_hashtags', []),
                'strengths': peer_grok.get('strengths', []),
                'weaknesses': peer_grok.get('weaknesses_for_growth', [])
            })
        
        # Build comprehensive analysis prompt
        prompt = self._build_analysis_prompt(
            user_handle,
            user_followers,
            user_grok,
            peer_summaries,
            num_insights
        )
        
        try:
            # Get Grok's deep analysis
            response = self.grok.complete_json(
                prompt=prompt,
                temperature=0.3,  # Lower temp for more focused analysis
                cost_tracker=self.cost_tracker
            )
            
            # Validate response structure
            if not self._validate_response(response):
                raise ValueError("Invalid response structure from Grok")
            
            logger.info("✅ Deep analysis complete")
            return response
            
        except GrokAPIError as e:
            logger.error(f"Grok API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            raise
    
    def _build_analysis_prompt(
        self,
        user_handle: str,
        user_followers: int,
        user_grok: Dict,
        peer_summaries: List[Dict],
        num_insights: int
    ) -> str:
        """Build comprehensive analysis prompt with detailed metrics"""
        
        # Calculate peer averages for comparison
        avg_peer_posts = sum(p['posts_per_week'] for p in peer_summaries) / len(peer_summaries) if peer_summaries else 0
        avg_peer_likes = sum(p['likes_per_post'] for p in peer_summaries) / len(peer_summaries) if peer_summaries else 0
        avg_peer_views = sum(p['views_per_post'] for p in peer_summaries) / len(peer_summaries) if peer_summaries else 0
        avg_peer_growth = sum(p['growth_rate'] for p in peer_summaries) / len(peer_summaries) if peer_summaries else 0
        
        # Format user data
        user_posts = user_grok.get('posting_frequency_per_week', 0)
        user_likes = user_grok.get('average_likes_per_post', 0)
        user_views = user_grok.get('average_views_per_post', 0)
        user_growth = user_grok.get('estimated_monthly_follower_growth_percent', 0)
        
        user_data = f"""
    USER PROFILE: @{user_handle}
    Followers: {user_followers:,}
    Niche: {user_grok.get('primary_niche', 'N/A')}
    Posts/Week: {user_posts} (Peers: {avg_peer_posts:.1f})
    Avg Likes: {user_likes} (Peers: {avg_peer_likes:.0f})
    Avg Views: {user_views} (Peers: {avg_peer_views:.0f})
    Growth: {user_growth}%/month (Peers: {avg_peer_growth:.1f}%/month)
    Visual Content: {user_grok.get('visual_content_ratio', 'medium')}
    Content Style: {user_grok.get('content_style', 'N/A')}
    """
        
        # Format peer data
        peers_data = ""
        for i, peer in enumerate(peer_summaries, 1):
            peers_data += f"""
    PEER {i}: @{peer['handle']} ({peer['followers']:,} followers)
    Posts/Week: {peer['posts_per_week']} | Likes: {peer['likes_per_post']} | Growth: {peer['growth_rate']}%/month
    Style: {peer['style']}
    Visual: {peer['visual_ratio']}
    """
        
        prompt = f"""You are an expert X/Twitter growth analyst. Generate 5-8 SPECIFIC, actionable insights with NUMBERS.

    {user_data}

    TOP PEERS (Growing Faster):
    {peers_data}

    Analyze the gaps and generate insights covering:
    1. Posting frequency and timing
    2. Visual content usage (images, charts, videos)
    3. Content format (threads vs single tweets)
    4. Engagement tactics (questions, CTAs, hooks)
    5. Topic strategy and trending participation
    6. Hashtag and formatting patterns

    Return ONLY valid JSON (no markdown):

    {{
      "growth_score": {user_growth},
      "growth_score_explanation": "You're posting {user_posts}x/week vs peers' {avg_peer_posts:.0f}x/week. Your {user_growth}% monthly growth trails peers' {avg_peer_growth:.1f}%.",
      
      "insights": [
        {{
          "title": "Increase Posting to 3x Per Day",
          "category": "posting_frequency",
          "priority": "critical",
          "current_state": "You post {user_posts}x/week ({user_posts/7:.1f}/day), getting {user_likes} avg likes",
          "peer_state": "Top peers post {avg_peer_posts:.1f}x/week ({avg_peer_posts/7:.1f}/day), getting {avg_peer_likes:.0f} avg likes",
          "gap_impact": "Posting {((avg_peer_posts - user_posts) / user_posts * 100):.0f}% less means {((avg_peer_posts - user_posts) / user_posts * 100):.0f}% fewer growth opportunities",
          "action": "Post at 9 AM, 2 PM, and 7 PM EST. Batch-create content on Sundays. Track engagement patterns for 2 weeks.",
          "expected_result": "Reach {int(avg_peer_likes / user_likes * 100 - 100) if user_likes > 0 else 100}% more people, gain ~{int((avg_peer_growth - user_growth) / 100 * user_followers)} followers/month",
          "measurement": "Compare next 20 posts to your current {user_likes} avg likes",
          "metrics": {{
            "current_value": {user_posts},
            "target_value": {avg_peer_posts:.1f},
            "gap_percentage": {((avg_peer_posts - user_posts) / user_posts * 100) if user_posts > 0 else 100:.0f},
            "potential_gain_followers": {int((avg_peer_growth - user_growth) / 100 * user_followers)}
          }}
        }},
        {{
          "title": "Add Visual Content to 70% of Posts",
          "category": "visual_content",
          "priority": "high",
          "current_state": "Your visual content ratio is {user_grok.get('visual_content_ratio', 'low')}",
          "peer_state": "Peers use high visual content (images, charts, infographics) in 70%+ of posts",
          "gap_impact": "Visual posts get 3-4x more engagement on X. You're leaving engagement on the table.",
          "action": "Next 10 posts: Add 1 relevant image/chart/screenshot. Use Canva for quick graphics. Post progress charts weekly.",
          "expected_result": "Boost engagement 2-3x on visual posts vs text-only",
          "measurement": "Track engagement rate: visual posts vs text-only posts",
          "metrics": {{
            "current_visual_pct": 30,
            "target_visual_pct": 70,
            "expected_engagement_boost": 200,
            "potential_reach_increase": 150
          }}
        }}
      ],
      
      "quick_wins": [
        "Tomorrow: Post at 9 AM, 2 PM, 7 PM (test peer timing)",
        "This week: Add images to your next 5 posts",
        "Next post: End with a question (boosts replies 3x)"
      ],
      
      "peer_standout_tactics": [
        "@{peer_summaries[0]['handle'] if peer_summaries else 'peer1'}: Posts {peer_summaries[0]['posts_per_week'] if peer_summaries else 20}x/week with {peer_summaries[0]['visual_ratio'] if peer_summaries else 'high'} visual content"
      ]
    }}

    CRITICAL RULES:
    - Use EXACT numbers from data
    - Every insight needs metrics object with numbers
    - Calculate gap_percentage and potential gains
    - Be specific: "Post 3x/day" not "post more"
    - Focus on TOP 5-8 highest-impact changes
    """
        
        return prompt
    
    def _validate_response(self, response: Dict) -> bool:
        """
        Validate that Grok returned proper structure
        Focus on essential fields only
        """
        # Only require the essential fields
        required_keys = [
            'growth_score',
            'insights'
        ]
        
        for key in required_keys:
            if key not in response:
                logger.error(f"Missing required key: {key}")
                return False
        
        # Validate insights structure
        insights = response.get('insights', [])
        if not isinstance(insights, list) or len(insights) == 0:
            logger.error("Invalid insights structure - must be non-empty array")
            return False
        
        # Check that each insight has required fields
        for i, insight in enumerate(insights):
            required_insight_fields = ['title', 'action']
            for field in required_insight_fields:
                if field not in insight:
                    logger.warning(f"Insight {i} missing field: {field}")
        
        logger.info(f"✅ Response validation passed with {len(insights)} insights")
        return True


# Test function
def test_insights_generator():
    """Test insights generation with sample data"""
    
    # Sample user profile
    user_profile = {
        'handle': 'testuser',
        'basic_metrics': {'followers_count': 5000},
        'grok_profile': {
            'primary_niche': 'SaaS marketing and growth',
            'secondary_topics': ['content marketing', 'SEO', 'social media'],
            'content_style': 'educational threads with occasional tips',
            'posting_frequency_per_week': 7,
            'average_likes_per_post': 15,
            'average_views_per_post': 500,
            'estimated_monthly_follower_growth_percent': 3,
            'visual_content_ratio': 'medium',
            'language_mix': 'English 100%',
            'key_hashtags': ['#SaaS', '#Marketing'],
            'strengths': ['good writing', 'clear explanations'],
            'weaknesses_for_growth': ['inconsistent posting', 'minimal visual content']
        }
    }
    
    # Sample peer profiles
    peer_profiles = [
        {
            'handle': 'peer1',
            'basic_metrics': {'followers_count': 15000},
            'grok_profile': {
                'primary_niche': 'SaaS growth strategies',
                'secondary_topics': ['marketing', 'product', 'analytics'],
                'content_style': 'data-driven threads with charts',
                'posting_frequency_per_week': 18,
                'average_likes_per_post': 120,
                'average_views_per_post': 5000,
                'estimated_monthly_follower_growth_percent': 12,
                'visual_content_ratio': 'high',
                'key_hashtags': ['#SaaS', '#Growth', '#Data'],
                'strengths': ['consistent posting', 'visual content', 'data storytelling'],
                'weaknesses_for_growth': ['could engage more with comments']
            }
        },
        {
            'handle': 'peer2',
            'basic_metrics': {'followers_count': 12000},
            'grok_profile': {
                'primary_niche': 'Marketing automation',
                'secondary_topics': ['tools', 'workflows', 'growth hacks'],
                'content_style': 'tactical how-to threads',
                'posting_frequency_per_week': 15,
                'average_likes_per_post': 90,
                'average_views_per_post': 4000,
                'estimated_monthly_follower_growth_percent': 10,
                'visual_content_ratio': 'high',
                'key_hashtags': ['#MarketingAutomation', '#GrowthHacks'],
                'strengths': ['actionable content', 'tools/screenshots'],
                'weaknesses_for_growth': ['could diversify topics more']
            }
        }
    ]
    
    print("\n🧪 Testing Insights Generator\n")
    print("="*70)
    
    try:
        generator = InsightsGenerator()
        result = generator.generate_insights(user_profile, peer_profiles, num_insights=3)
        
        print(f"\n📊 GROWTH SCORE: {result['growth_score']}/10")
        print(f"Explanation: {result.get('growth_score_explanation', 'N/A')}")
        
        print(f"\n📈 POSTING ANALYSIS:")
        posting = result.get('posting_analysis', {})
        print(f"   Gap: {posting.get('gap', 'N/A')}")
        print(f"   Impact: {posting.get('impact', 'N/A')}")
        
        print(f"\n💡 INSIGHTS ({len(result['insights'])}):")
        for i, insight in enumerate(result['insights'], 1):
            print(f"\n{i}. {insight.get('title', 'N/A')} ({insight.get('priority', 'N/A')})")
            print(f"   Current: {insight.get('current_state', 'N/A')}")
            print(f"   Action: {insight.get('action', 'N/A')}")
            print(f"   Expected: {insight.get('expected_result', 'N/A')}")
        
        print("\n" + "="*70)
        print("✅ Test complete!")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_insights_generator()