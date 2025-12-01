# ai/peer_insights_generator.py
from typing import Dict, List
from ai.grok_client import GrokClient
from data.twitter_client import TwitterAPIClient
import json
import logging

logger = logging.getLogger(__name__)


class PeerInsightsGenerator:
    """
    Generate detailed insights for individual peer accounts
    """
    
    def __init__(self, cost_tracker=None):
        self.grok = GrokClient()
        self.twitter = TwitterAPIClient(cost_tracker)
        self.cost_tracker = cost_tracker
        logger.info("PeerInsightsGenerator initialized")
    
    def analyze_peer(
        self,
        user_profile: Dict,
        peer_profile: Dict,
        fetch_tweets: bool = True
    ) -> Dict:
        """
        Deep analysis of individual peer using REAL tweets
        """
        peer_handle = peer_profile['handle']
        logger.info(f"Analyzing peer @{peer_handle} in detail")
        
        # Fetch REAL example tweets
        example_tweets = []
        if fetch_tweets:
            try:
                tweets = self.twitter.get_user_tweets(peer_handle, max_results=10)
                example_tweets = tweets[:5] if tweets else []
                logger.info(f"Fetched {len(example_tweets)} real tweets from @{peer_handle}")
            except Exception as e:
                logger.warning(f"Could not fetch tweets for @{peer_handle}: {e}")
                # Try without tweets
        
        # If we have no tweets, return basic insights
        if not example_tweets or len(example_tweets) == 0:
            logger.warning(f"No tweets available for @{peer_handle}, generating basic insights")
            return {
                'unique_characteristics': [
                    f"Growing at {peer_profile.get('grok_profile', {}).get('estimated_monthly_follower_growth_percent', 0):.1f}% per month",
                    f"Has {peer_profile['basic_metrics']['followers_count']:,} followers",
                    f"Posts {peer_profile.get('grok_profile', {}).get('posting_frequency_per_week', 0)}x per week"
                ],
                'what_they_do_differently': [],
                'tactical_insights': [],
                'example_tweets': []
            }
        
        # Generate insights based on REAL tweets
        insights = self._generate_peer_insights(
            user_profile,
            peer_profile,
            example_tweets
        )
        
        return {
            **insights,
            'example_tweets': example_tweets[:3]  # Include real tweets
        }
    
    def _generate_peer_insights(
        self,
        user_profile: Dict,
        peer_profile: Dict,
        example_tweets: List[Dict]
    ) -> Dict:
        """Use Grok to analyze REAL tweets"""
        
        user_grok = user_profile.get('grok_profile', {})
        peer_grok = peer_profile.get('grok_profile', {})
        
        # Format REAL tweets for analysis
        tweets_text = ""
        if example_tweets:
            for i, tweet in enumerate(example_tweets[:5], 1):
                metrics = tweet.get('public_metrics', {})
                likes = metrics.get('like_count', 0)
                retweets = metrics.get('retweet_count', 0)
                tweets_text += f"\nTweet {i} ({likes} likes, {retweets} RTs):\n{tweet.get('text', '')[:300]}\n"
        
        prompt = f"""Analyze REAL DATA from @{peer_profile['handle']} vs @{user_profile['handle']}.

    USER (@{user_profile['handle']}):
    - Followers: {user_profile['basic_metrics']['followers_count']:,}
    - Posts/Week: {user_grok.get('posting_frequency_per_week', 0)}
    - Avg Likes: {user_grok.get('average_likes_per_post', 0)}

    PEER (@{peer_profile['handle']}):
    - Followers: {peer_profile['basic_metrics']['followers_count']:,}
    - Posts/Week: {peer_grok.get('posting_frequency_per_week', 0)}
    - Avg Likes: {peer_grok.get('average_likes_per_post', 0)}

    REAL TWEETS FROM @{peer_profile['handle']}:
    {tweets_text}

    Analyze these ACTUAL tweets and find SPECIFIC patterns. Return ONLY valid JSON:

    {{
    "unique_characteristics": [
        "SPECIFIC observation from the tweets above (e.g., 'Uses bullet points in 3 of 5 tweets')",
        "SPECIFIC pattern (e.g., 'Posts market charts at specific times')",
        "SPECIFIC tactic (e.g., 'Ends 4 of 5 tweets with questions')"
    ],
    "what_they_do_differently": [
        {{
        "category": "Posting Frequency",
        "user_approach": "Posts {user_grok.get('posting_frequency_per_week', 0)}x/week",
        "peer_approach": "Posts {peer_grok.get('posting_frequency_per_week', 0)}x/week",
        "impact": "Calculate the difference",
        "example": "Reference a specific tweet from above"
        }}
    ],
    "tactical_insights": [
        {{
        "tactic": "Specific tactic from the tweets",
        "how_they_do_it": "Based on the actual tweets above",
        "why_it_works": "Explain based on engagement numbers",
        "how_to_copy": "Actionable steps",
        "expected_result": "Based on their actual performance"
        }}
    ]
    }}

    CRITICAL: Base ALL insights on the ACTUAL tweets provided. No generic advice!"""
        
        try:
            response = self.grok.complete_json(
                prompt=prompt,
                temperature=0.2,
                cost_tracker=self.cost_tracker
            )
            
            logger.info(f"✅ Generated unique insights for @{peer_profile['handle']}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate peer insights: {e}")
            return {
                'unique_characteristics': [],
                'what_they_do_differently': [],
                'tactical_insights': []
            }