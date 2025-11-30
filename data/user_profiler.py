# data/user_profiler.py
from typing import Dict, List, Optional
import json
from datetime import datetime
import logging
from ai.grok_client import GrokClient, GrokAPIError

logger = logging.getLogger(__name__)


class UserProfiler:
    """
    Analyzes user profiles using Grok API with smart tweet fetching
    """
    
    def __init__(self, cost_tracker=None):
        """Initialize profiler with Grok client"""
        try:
            self.grok = GrokClient()
            self.cost_tracker = cost_tracker
            logger.info("UserProfiler initialized with Grok AI")
        except Exception as e:
            logger.error(f"Could not initialize Grok client: {e}")
            raise
    
    def analyze_user(
        self, 
        user_data: Dict, 
        tweets: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Generate comprehensive user profile using Grok
        
        Args:
            user_data: User profile from X API
            tweets: Optional list of recent tweets (only needed for small accounts)
        
        Returns:
            Dict with analysis results including Grok-enhanced profile
        """
        handle = user_data.get('username', 'unknown')
        followers = user_data.get('public_metrics', {}).get('followers_count', 0)
        
        logger.info(f"Analyzing user @{handle} ({followers:,} followers) with Grok")
        
        try:
            # Determine if we need tweets
            needs_tweets = self._should_fetch_tweets(followers)
            
            if needs_tweets and not tweets:
                raise ValueError(f"Account @{handle} has {followers:,} followers and needs tweets for profiling")
            
            # Build appropriate prompt based on account size
            if needs_tweets:
                prompt = self._build_profile_prompt_with_tweets(user_data, tweets)
                logger.info(f"Profiling with {len(tweets)} tweets (small account)")
            else:
                prompt = self._build_profile_prompt_handle_only(user_data)
                logger.info(f"Profiling by handle only (famous account)")
            
            # Get Grok analysis
            grok_profile = self.grok.complete_json(
                prompt=prompt,
                temperature=0.0,
                cost_tracker=self.cost_tracker
            )
            
            # Validate response
            if not grok_profile or 'handle' not in grok_profile:
                raise ValueError("Invalid Grok response structure")
            
            logger.info(f"✅ Grok analysis complete for @{handle}")
            logger.info(f"   Primary niche: {grok_profile.get('primary_niche')}")
            logger.info(f"   Growth trend: {grok_profile.get('growth_trend_last_30_days')}")
            
            # Build complete profile
            profile = {
                'handle': handle,
                'user_id': user_data.get('id'),
                'name': user_data.get('name'),
                'bio': user_data.get('description', ''),
                'profile_image': user_data.get('profile_image_url'),
                'basic_metrics': self._extract_basic_metrics(user_data),
                'grok_profile': grok_profile,  # Full Grok analysis
                # Legacy fields for backward compatibility
                'niche': self._extract_primary_niche(grok_profile),
                'content_style': self._build_content_style(grok_profile),
                'posting_rhythm': self._build_posting_rhythm(grok_profile),
                'engagement_baseline': self._build_engagement_baseline(grok_profile),
                'growth_velocity': self._build_growth_velocity(grok_profile)
            }
            
            return profile
            
        except GrokAPIError as e:
            logger.error(f"Grok API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in user profiling: {e}")
            raise
    
    def _should_fetch_tweets(self, followers_count: int) -> bool:
        """
        Determine if we need to fetch tweets based on account size
        
        Famous accounts (>100K): Grok knows them already
        Small accounts (<100K): Need tweets to profile
        """
        FAMOUS_THRESHOLD = 100000
        return followers_count < FAMOUS_THRESHOLD
    
    def _build_profile_prompt_with_tweets(self, user_data: Dict, tweets: List[Dict]) -> str:
        """
        Build prompt WITH tweets for small/unknown accounts
        """
        handle = user_data.get('username', '')
        bio = user_data.get('description', '')
        followers = user_data.get('public_metrics', {}).get('followers_count', 0)
        following = user_data.get('public_metrics', {}).get('following_count', 0)
        total_posts = user_data.get('public_metrics', {}).get('tweet_count', 0)
        
        # Format tweets as JSON array
        recent_posts = []
        for tweet in tweets[:40]:  # Use up to 40 tweets
            post = {
                'text': tweet.get('text', ''),
                'likes': tweet.get('public_metrics', {}).get('like_count', 0),
                'reposts': tweet.get('public_metrics', {}).get('retweet_count', 0),
                'replies': tweet.get('public_metrics', {}).get('reply_count', 0),
                'views': tweet.get('public_metrics', {}).get('view_count', 0),
                'created_at': tweet.get('created_at', '')
            }
            recent_posts.append(post)
        
        recent_posts_json = json.dumps(recent_posts, indent=2)
        
        prompt = f"""You are an expert X/Twitter analyst. Analyze this user and return ONLY a valid JSON object. No markdown, no explanations, no extra text.

User data:
Handle: {handle}
Bio: {bio}
Followers: {followers}
Following: {following}
Total posts: {total_posts}

Recent posts (newest first) as JSON array:
{recent_posts_json}

Return exactly this JSON structure:

{{
  "handle": "{handle}",
  "followers": {followers},
  "primary_niche": "one-sentence summary of main content pillar",
  "secondary_topics": ["topic1", "topic2", "topic3", "max 5"],
  "content_style": "e.g. threads, charts, memes, one-liners, motivational, educational, political commentary",
  "average_likes_per_post": 12.4,
  "average_views_per_post": 1847,
  "growth_trend_last_30_days": "growing fast" | "growing steadily" | "stagnant" | "declining",
  "estimated_monthly_follower_growth_percent": 8.5,
  "language_mix": "English 90%, Spanish 10%" or similar,
  "posting_frequency_per_week": 12,
  "visual_content_ratio": "high" | "medium" | "low",
  "key_hashtags": ["#hashtag1", "#hashtag2", "max 8"],
  "strengths": ["max 4 short bullets"],
  "weaknesses_for_growth": ["max 4 short bullets"]
}}"""
        
        return prompt
    
    def _build_profile_prompt_handle_only(self, user_data: Dict) -> str:
        """
        Build prompt WITHOUT tweets for famous accounts (Grok knows them)
        """
        handle = user_data.get('username', '')
        bio = user_data.get('description', '')
        followers = user_data.get('public_metrics', {}).get('followers_count', 0)
        
        prompt = f"""You are an expert X/Twitter analyst. You have knowledge of famous X accounts.

Analyze @{handle} using your built-in knowledge. Return ONLY a valid JSON object. No markdown, no explanations.

Account info:
Handle: {handle}
Bio: {bio}
Current Followers: {followers}

Use your knowledge of this account to provide a complete profile.

Return exactly this JSON structure:

{{
  "handle": "{handle}",
  "followers": {followers},
  "primary_niche": "one-sentence summary of main content pillar",
  "secondary_topics": ["topic1", "topic2", "topic3", "max 5"],
  "content_style": "e.g. threads, charts, memes, one-liners, motivational, educational, political commentary",
  "average_likes_per_post": 12.4,
  "average_views_per_post": 1847,
  "growth_trend_last_30_days": "growing fast" | "growing steadily" | "stagnant" | "declining",
  "estimated_monthly_follower_growth_percent": 8.5,
  "language_mix": "English 90%, Spanish 10%" or similar,
  "posting_frequency_per_week": 12,
  "visual_content_ratio": "high" | "medium" | "low",
  "key_hashtags": ["#hashtag1", "#hashtag2", "max 8"],
  "strengths": ["max 4 short bullets"],
  "weaknesses_for_growth": ["max 4 short bullets"]
}}"""
        
        return prompt
    
    def _extract_basic_metrics(self, user_data: Dict) -> Dict:
        """Extract basic account metrics"""
        metrics = user_data.get('public_metrics', {})
        
        followers = metrics.get('followers_count', 0)
        following = metrics.get('following_count', 0)
        
        return {
            'followers_count': followers,
            'following_count': following,
            'tweet_count': metrics.get('tweet_count', 0),
            'listed_count': metrics.get('listed_count', 0),
            'follower_following_ratio': round(followers / following, 2) if following > 0 else float(followers)
        }
    
    def _extract_primary_niche(self, grok_profile: Dict) -> str:
        """Extract primary niche from Grok profile"""
        primary = grok_profile.get('primary_niche', 'other')
        
        # Try to map to our niche categories
        niche_keywords = {
            'tech': ['technology', 'software', 'developer', 'programming', 'ai', 'machine learning'],
            'business': ['business', 'entrepreneur', 'startup', 'founder', 'saas'],
            'marketing': ['marketing', 'content', 'seo', 'branding'],
            'finance': ['finance', 'investing', 'trading', 'stocks', 'crypto'],
            'health': ['health', 'fitness', 'wellness', 'nutrition'],
        }
        
        primary_lower = primary.lower()
        for niche, keywords in niche_keywords.items():
            if any(kw in primary_lower for kw in keywords):
                return niche
        
        return 'other'
    
    def _build_content_style(self, grok_profile: Dict) -> Dict:
        """Build content style dict from Grok profile"""
        visual_ratio = grok_profile.get('visual_content_ratio', 'medium')
        visual_map = {'high': 70, 'medium': 40, 'low': 10}
        
        return {
            'thread_percentage': 0,
            'media_percentage': visual_map.get(visual_ratio, 40),
            'link_percentage': 0,
            'question_percentage': 0,
            'avg_tweet_length': 0,
            'content_mix': {
                'threads': 0,
                'media_posts': 0,
                'link_posts': 0,
                'questions': 0
            }
        }
    
    def _build_posting_rhythm(self, grok_profile: Dict) -> Dict:
        """Build posting rhythm dict from Grok profile"""
        posts_per_week = grok_profile.get('posting_frequency_per_week', 0)
        return {
            'posts_per_week': posts_per_week,
            'consistency_score': min(100, int((posts_per_week / 7) * 100)),
            'date_range_days': 30,
            'total_analyzed': 40
        }
    
    def _build_engagement_baseline(self, grok_profile: Dict) -> Dict:
        """Build engagement baseline from Grok profile"""
        avg_likes = grok_profile.get('average_likes_per_post', 0)
        followers = grok_profile.get('followers', 1)
        
        engagement_rate = (avg_likes / followers) * 100 if followers > 0 else 0
        
        return {
            'avg_likes': avg_likes,
            'avg_retweets': 0,
            'avg_replies': 0,
            'engagement_rate': round(engagement_rate, 2),
            'total_engagements': int(avg_likes),
            'engagement_per_tweet': avg_likes
        }
    
    def _build_growth_velocity(self, grok_profile: Dict) -> Dict:
        """Build growth velocity from Grok profile"""
        monthly_growth_pct = grok_profile.get('estimated_monthly_follower_growth_percent', 0)
        followers = grok_profile.get('followers', 0)
        estimated_growth = int(followers * (monthly_growth_pct / 100))
        
        return {
            'estimated_30d_growth': estimated_growth,
            'growth_rate_pct': monthly_growth_pct
        }


# Test function
def test_profiler():
    """Test the user profiler"""
    
    # Test 1: Famous account (no tweets needed)
    print("\n1️⃣ Testing famous account (no tweets)...")
    famous_user = {
        'username': 'naval',
        'id': '12345',
        'name': 'Naval',
        'description': 'Angel investor. Co-founder @AngelList',
        'public_metrics': {
            'followers_count': 2100000,
            'following_count': 0,
            'tweet_count': 12000
        }
    }
    
    try:
        profiler = UserProfiler()
        profile = profiler.analyze_user(famous_user, tweets=None)
        print(f"   ✅ Success! Niche: {profile['grok_profile']['primary_niche']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 2: Small account (tweets needed)
    print("\n2️⃣ Testing small account (with tweets)...")
    small_user = {
        'username': 'smallaccount',
        'id': '67890',
        'name': 'Small Account',
        'description': 'Content creator',
        'public_metrics': {
            'followers_count': 5000,
            'following_count': 500,
            'tweet_count': 1200
        }
    }
    
    sample_tweets = [
        {
            'text': 'Building in public!',
            'created_at': '2024-01-15T10:30:00Z',
            'public_metrics': {'like_count': 50, 'retweet_count': 10, 'reply_count': 5}
        }
    ] * 20
    
    try:
        profile = profiler.analyze_user(small_user, tweets=sample_tweets)
        print(f"   ✅ Success! Niche: {profile['grok_profile']['primary_niche']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")


if __name__ == "__main__":
    test_profiler()