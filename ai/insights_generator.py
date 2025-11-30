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
        logger.info("InsightsGenerator initialized with Grok AI")
    
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
        """
        Build comprehensive analysis prompt with strict guidelines
        """
        
        # Format user data
        user_data = f"""
USER PROFILE: @{user_handle}
Followers: {user_followers:,}
Primary Niche: {user_grok.get('primary_niche', 'N/A')}
Topics: {json.dumps(user_grok.get('secondary_topics', []))}
Content Style: {user_grok.get('content_style', 'N/A')}
Posts/Week: {user_grok.get('posting_frequency_per_week', 0)}
Avg Likes: {user_grok.get('average_likes_per_post', 0)}
Avg Views: {user_grok.get('average_views_per_post', 0)}
Growth Rate: {user_grok.get('estimated_monthly_follower_growth_percent', 0)}% per month
Visual Content: {user_grok.get('visual_content_ratio', 'medium')}
Language: {user_grok.get('language_mix', 'N/A')}
Hashtags Used: {json.dumps(user_grok.get('key_hashtags', []))}
Strengths: {json.dumps(user_grok.get('strengths', []))}
Weaknesses: {json.dumps(user_grok.get('weaknesses_for_growth', []))}
"""
        
        # Format peer data
        peers_data = ""
        for i, peer in enumerate(peer_summaries, 1):
            peers_data += f"""
PEER {i}: @{peer['handle']} ({peer['followers']:,} followers)
Niche: {peer['niche']}
Topics: {json.dumps(peer['topics'])}
Style: {peer['style']}
Posts/Week: {peer['posts_per_week']}
Likes: {peer['likes_per_post']} | Views: {peer['views_per_post']}
Growth: {peer['growth_rate']}% per month
Visual Content: {peer['visual_ratio']}
Hashtags: {json.dumps(peer['hashtags'][:5])}
Strengths: {json.dumps(peer['strengths'])}
"""
        
        # Main analysis prompt
        prompt = f"""You are an expert X/Twitter growth analyst. Perform a DEEP COMPARATIVE ANALYSIS between the user and their successful peers.

{user_data}

SUCCESSFUL PEERS (Growing Faster):
{peers_data}

ANALYSIS REQUIREMENTS:

1. POSTING PATTERNS ANALYSIS
   - Compare posting frequency (exact numbers)
   - Identify optimal posting times/days (if patterns visible)
   - Analyze consistency vs sporadic posting
   - Compare response to trending topics

2. CONTENT TYPE & STRUCTURE ANALYSIS
   - Single tweets vs threads (which performs better for peers?)
   - Media usage: images, videos, charts, infographics
   - Link sharing patterns and frequency
   - Question-based engagement tactics
   - Poll usage and effectiveness
   - Tweet length patterns (short punchy vs long-form)

3. NICHE & TOPIC DISTRIBUTION
   - What % of content goes to which topics (estimate based on secondary_topics)
   - Topic diversification vs specialization
   - Trending topic participation
   - Educational vs entertainment vs promotional content mix

4. TWEET STRUCTURE & FORMATTING
   - Use of emojis and their placement
   - Hashtag strategy (quantity, placement, types)
   - Thread hooks and storytelling structure
   - Call-to-action patterns
   - Personal stories vs data/facts ratio
   - Bullet points, numbered lists, formatting tricks

5. UNIQUE CHARACTERISTICS
   - What makes each peer stand out?
   - Signature styles or formats
   - Engagement tactics (replying, quote tweeting, etc.)
   - Community building approaches

STRICT OUTPUT FORMAT (return ONLY valid JSON, no markdown):

{{
  "growth_score": 6.5,
  "growth_score_explanation": "Your 3% monthly growth trails peers' 12-15% average. You're in the bottom 30th percentile of your cohort.",
  
  "posting_analysis": {{
    "user_pattern": {{
      "posts_per_week": 7,
      "consistency": "low",
      "description": "Posts sporadically, 2-3 times some days then silent for 2-3 days"
    }},
    "peer_pattern": {{
      "posts_per_week": 18,
      "consistency": "high",
      "description": "Posts 2-3 times daily at consistent times (9 AM, 2 PM, 7 PM EST)"
    }},
    "gap": "You post 61% less frequently than successful peers",
    "impact": "Low posting frequency means algorithm doesn't prioritize your content and followers forget about you between posts"
  }},
  
  "content_analysis": {{
    "user_style": {{
      "thread_usage": "10%",
      "media_usage": "40%",
      "link_frequency": "high (75% of posts)",
      "tweet_length": "medium (150 chars avg)",
      "unique_traits": ["uses links heavily", "minimal visual content"]
    }},
    "peer_style": {{
      "thread_usage": "25%",
      "media_usage": "70%",
      "link_frequency": "low (20% of posts)",
      "tweet_length": "varied (50-280 chars)",
      "unique_traits": ["heavy infographic use", "daily charts", "storytelling threads"]
    }},
    "gap": "You use 43% less visual content and 3.75x more external links than peers",
    "impact": "Link-heavy posts get deprioritized by X algorithm. Visual content gets 3x more engagement."
  }},
  
  "topic_analysis": {{
    "user_distribution": {{
      "primary_focus": "70%",
      "secondary_topics": "30%",
      "trending_participation": "low"
    }},
    "peer_distribution": {{
      "primary_focus": "60%",
      "secondary_topics": "30%",
      "trending_participation": "high (10%)"
    }},
    "gap": "You focus too narrowly on primary niche; peers diversify with trending topics",
    "impact": "Trending topic participation can 10x reach but you're missing these opportunities"
  }},
  
  "structure_analysis": {{
    "user_formatting": {{
      "emoji_usage": "minimal",
      "hashtag_strategy": "few hashtags, generic",
      "thread_hooks": "weak or none",
      "cta_presence": "rare"
    }},
    "peer_formatting": {{
      "emoji_usage": "strategic (for visual breaks and emphasis)",
      "hashtag_strategy": "3-5 niche-specific hashtags per post",
      "thread_hooks": "strong curiosity gaps, numbers, promises",
      "cta_presence": "most posts end with question or action prompt"
    }},
    "gap": "Your posts lack engagement hooks and clear CTAs that peers use effectively",
    "impact": "Without hooks and CTAs, engagement rates drop 50-70%"
  }},
  
  "insights": [
    {{
      "title": "Triple Your Posting Frequency",
      "category": "posting_pattern",
      "priority": "critical",
      "current_state": "You post 7x per week with sporadic timing",
      "peer_state": "Successful peers post 18x per week at consistent times",
      "gap_impact": "You're reaching 61% fewer people. Algorithm deprioritizes inconsistent accounts.",
      "action": "Post 15x per week minimum: 2-3 posts daily at 9 AM, 2 PM, 7 PM EST. Batch-create content on Sundays.",
      "expected_result": "30-50% increase in reach within 30 days",
      "measurement": "Track weekly impressions and engagement rate"
    }},
    {{
      "title": "Shift to Visual-First Content",
      "category": "content_type",
      "priority": "high",
      "current_state": "Only 40% of posts include media; 75% include external links",
      "peer_state": "Peers use media in 70% of posts and links in only 20%",
      "gap_impact": "Link-heavy posts get 50-70% less reach. You're leaving 3x engagement on the table.",
      "action": "Create/add charts, infographics, or images to 65% of posts. Reduce link posts to 25%. Put links in first reply instead.",
      "expected_result": "2-3x engagement boost on visual posts",
      "measurement": "Compare engagement rate on visual vs text-only posts"
    }},
    {{
      "title": "Ride Trending Topics Weekly",
      "category": "topic_strategy",
      "priority": "medium",
      "current_state": "You focus 70% on core niche, ignore trending topics",
      "peer_state": "Peers allocate 10% of posts to trending topics in their niche",
      "gap_impact": "Missing 10x reach opportunities when topics trend",
      "action": "Every Monday, identify 2-3 trending topics in your niche. Create 2-3 posts connecting trends to your expertise.",
      "expected_result": "1-2 viral posts per month reaching 10x normal audience",
      "measurement": "Track posts that exceed 3x your average views"
    }}
  ],
  
  "quick_wins": [
    "Add an image or chart to your next 5 posts",
    "Post at 9 AM and 7 PM EST tomorrow (test optimal times)",
    "End your next 3 posts with a question to boost replies"
  ],
  
  "peer_standout_tactics": [
    "@peer1 posts daily market charts at 9 AM - creates anticipation and routine",
    "@peer2 shares personal failure stories in threads - builds authentic connection",
    "@peer3 uses numbered lists and emojis for visual appeal and scannability"
  ]
}}

CRITICAL RULES:
- Use EXACT numbers from the data provided
- Be specific, not generic ("post 15x per week" not "post more often")
- Compare apples to apples (same metrics for user and peers)
- Focus on ACTIONABLE differences, not just observations
- Growth score must be 0-10 based on comparison with peers
- Every insight needs: current state, peer state, gap, action, expected result
- Return ONLY valid JSON, no markdown formatting, no extra text

Generate the analysis now:"""
        
        return prompt
    
    def _validate_response(self, response: Dict) -> bool:
        """
        Validate that Grok returned proper structure
        """
        required_keys = [
            'growth_score',
            'posting_analysis',
            'content_analysis',
            'topic_analysis',
            'structure_analysis',
            'insights'
        ]
        
        for key in required_keys:
            if key not in response:
                logger.error(f"Missing required key: {key}")
                return False
        
        # Validate insights structure
        insights = response.get('insights', [])
        if not isinstance(insights, list) or len(insights) == 0:
            logger.error("Invalid insights structure")
            return False
        
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