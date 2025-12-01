# ai/peer_matcher.py
from typing import Dict, List, Optional
import json
import logging
from ai.grok_client import GrokClient, GrokAPIError
from db.models import PeerMatch
from db.connection import get_session

logger = logging.getLogger(__name__)


class PeerMatcher:
    """
    Grok-powered peer account matching system (optimized - no tweet fetching!)
    """
    
    def __init__(self, cost_tracker=None):
        self.grok = GrokClient()
        self.cost_tracker = cost_tracker
        logger.info("PeerMatcher initialized with Grok AI (optimized mode)")
    
    def find_peers(
        self,
        user_profile: Dict,
        count: int = 5,
        excluded_handles: set = None,  # NEW parameter
        save_to_db: bool = False,
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Find similar accounts using Grok AI + Twitter validation
        
        Args:
            excluded_handles: Set of handles to avoid (previously analyzed peers)
        """
        from data.twitter_client import TwitterAPIClient
        
        if excluded_handles is None:
            excluded_handles = set()
        
        logger.info(f"Finding {count} NEW peers (excluding {len(excluded_handles)} previous)")
        
        try:
            # STEP 1: Get peer suggestions from Grok (request more to account for exclusions)
            request_count = count * 3 + len(excluded_handles)
            suggested_handles = self._get_peer_suggestions_from_grok(
                user_profile, 
                request_count,
                excluded_handles  # Pass exclusions to Grok
            )
            
            logger.info(f"Grok suggested {len(suggested_handles)} handles")
            
            # STEP 2: Filter out excluded handles
            filtered_handles = [
                h for h in suggested_handles 
                if h.lower() not in excluded_handles
            ]
            
            logger.info(f"After filtering: {len(filtered_handles)} new handles to check")
            
            # STEP 3: Validate and fetch REAL data from Twitter
            twitter_client = TwitterAPIClient(self.cost_tracker)
            validated_peers = []
            
            for handle in filtered_handles:
                try:
                    # Get REAL user data from Twitter
                    user_data = twitter_client.get_user_by_handle(handle)
                    
                    if not user_data:
                        logger.warning(f"Could not fetch data for @{handle}")
                        continue
                    
                    # Check if follower count is in reasonable range
                    followers = user_data['public_metrics']['followers_count']
                    user_followers = user_profile['basic_metrics']['followers_count']
                    
                    # Filter: Must be 0.8x to 3x user's followers
                    if followers < user_followers * 0.8 or followers > user_followers * 3:
                        logger.info(f"Skipping @{handle} - {followers} followers (out of range)")
                        continue
                    
                    # Fetch REAL tweets
                    tweets = twitter_client.get_user_tweets(handle, max_results=20)
                    
                    if not tweets or len(tweets) < 5:
                        logger.warning(f"@{handle} has too few tweets ({len(tweets)})")
                        continue
                    
                    # Use UserProfiler to analyze with REAL data
                    from data.user_profiler import UserProfiler
                    profiler = UserProfiler(self.cost_tracker)
                    
                    peer_profile = profiler.analyze_user(user_data, tweets)
                    
                    # Calculate match score
                    peer_profile['match_score'] = self._calculate_match_score(
                        user_profile,
                        peer_profile
                    )
                    
                    peer_profile['match_reason'] = self._generate_match_reason(
                        user_profile,
                        peer_profile
                    )
                    
                    peer_profile['growth_edge'] = self._generate_growth_edge(
                        peer_profile
                    )
                    
                    validated_peers.append(peer_profile)
                    
                    logger.info(f"✅ Validated NEW peer @{handle}: {followers} followers")
                    
                    # Stop when we have enough
                    if len(validated_peers) >= count:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error validating @{handle}: {e}")
                    continue
            
            if len(validated_peers) == 0:
                logger.warning("No new valid peers found!")
                return []
            
            # Sort by match score
            validated_peers.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            
            # Take top N
            top_peers = validated_peers[:count]
            
            logger.info(f"✅ Returning {len(top_peers)} NEW validated peers")
            return top_peers
            
        except Exception as e:
            logger.error(f"Error in peer matching: {e}")
            raise
    def _get_peer_suggestions_from_grok(
        self, 
        user_profile: Dict, 
        count: int = 15,
        excluded_handles: set = None  # NEW parameter
    ) -> List[str]:
        """
        Get peer HANDLE suggestions from Grok (excluding previously analyzed ones)
        """
        if excluded_handles is None:
            excluded_handles = set()
        
        grok_profile = user_profile.get('grok_profile', {})
        
        handle = user_profile['handle']
        followers = user_profile['basic_metrics']['followers_count']
        primary_niche = grok_profile.get('primary_niche', 'general content')
        secondary_topics = json.dumps(grok_profile.get('secondary_topics', []))
        
        # Format excluded handles for prompt
        excluded_list = ", ".join([f"@{h}" for h in list(excluded_handles)[:20]])
        exclusion_text = f"\n\nDO NOT SUGGEST THESE (already analyzed): {excluded_list}" if excluded_handles else ""
        
        prompt = f"""You are an expert X/Twitter analyst. Suggest {count} REAL, DIFFERENT X account handles similar to @{handle}.

    USER: @{handle}
    - Followers: {followers:,}
    - Niche: {primary_niche}
    - Topics: {secondary_topics}

    CRITICAL REQUIREMENTS:
    - Return ONLY real, active X accounts that exist
    - Same niche + overlapping topics
    - Follower count: {int(followers * 0.8):,} to {int(followers * 3):,}
    - Must be actively posting (2025)
    - Do NOT make up accounts
    - Suggest DIFFERENT accounts than before{exclusion_text}

    Return ONLY a JSON array of NEW handles (no other text):

    {{"handles": ["handle1", "handle2", "handle3", ...]}}

    Example: {{"handles": ["naval", "elonmusk", "garyvee"]}}

    Be VERY careful - only suggest accounts you're confident exist and are DIFFERENT from the excluded list."""
        
        try:
            response = self.grok.complete_json(
                prompt=prompt,
                temperature=0.3,  # Slightly higher for more variety
                cost_tracker=self.cost_tracker
            )
            
            handles = response.get('handles', [])
            
            # Clean handles and filter out excluded ones
            cleaned = [
                h.replace('@', '').strip().lower() 
                for h in handles 
                if h and h.replace('@', '').strip().lower() not in excluded_handles
            ]
            
            logger.info(f"Grok suggested {len(cleaned)} NEW handles (filtered out {len(handles) - len(cleaned)} excluded)")
            return cleaned
            
        except Exception as e:
            logger.error(f"Grok suggestion failed: {e}")
            return self._get_fallback_suggestions(primary_niche, followers, excluded_handles)


    def _get_fallback_suggestions(self, niche: str, followers: int, excluded_handles: set = None) -> List[str]:
        """Fallback peer suggestions by niche (excluding previously used)"""
        
        if excluded_handles is None:
            excluded_handles = set()
        
        # Popular accounts by niche (real verified accounts)
        niche_accounts = {
            'finance': ['markets', 'WSJ', 'financialtimes', 'zerohedge', 'ReformedTrader', 'markets', 'YahooFinance', 'business', 'FT', 'economics'],
            'tech': ['techcrunch', 'verge', 'WIRED', 'Techmeme', 'BenedictEvans', 'arstechnica', 'engadget', 'TheNextWeb', 'ProductHunt'],
            'marketing': ['neilpatel', 'randfish', 'buffer', 'hootsuite', 'Marketingland', 'semrush', 'HubSpot', 'Unbounce', 'copyblogger'],
            'ai': ['AndrewYNg', 'ylecun', 'goodfellow_ian', 'hardmaru', 'fchollet', 'karpathy', 'lexfridman', 'emollick', 'sama'],
            'business': ['ycombinator', 'hnshah', 'paulg', 'jason', 'rrhoover', 'naval', 'balajis', 'patrick_oshag', 'BrentBeshore'],
        }
        
        # Try to match niche
        niche_lower = niche.lower()
        for key, accounts in niche_accounts.items():
            if key in niche_lower:
                # Filter out excluded
                filtered = [a for a in accounts if a.lower() not in excluded_handles]
                return filtered[:10]
        
        # Default popular business accounts (filtered)
        default_accounts = ['ycombinator', 'paulg', 'rrhoover', 'naval', 'balajis', 'jason', 'hnshah', 'sama', 'garyvee', 'JamesClear']
        filtered = [a for a in default_accounts if a.lower() not in excluded_handles]
        return filtered[:10]


    def _calculate_match_score(self, user_profile: Dict, peer_profile: Dict) -> float:
        """Calculate match score based on real data"""
        
        user_grok = user_profile.get('grok_profile', {})
        peer_grok = peer_profile.get('grok_profile', {})
        
        score = 0.0
        
        # Niche similarity (40 points)
        user_niche = user_grok.get('primary_niche', '').lower()
        peer_niche = peer_grok.get('primary_niche', '').lower()
        
        if user_niche in peer_niche or peer_niche in user_niche:
            score += 40
        
        # Topic overlap (30 points)
        user_topics = set(user_grok.get('secondary_topics', []))
        peer_topics = set(peer_grok.get('secondary_topics', []))
        overlap = len(user_topics & peer_topics)
        
        score += min(overlap * 10, 30)
        
        # Follower proximity (20 points)
        user_followers = user_profile['basic_metrics']['followers_count']
        peer_followers = peer_profile['basic_metrics']['followers_count']
        ratio = peer_followers / user_followers if user_followers > 0 else 1
        
        if 0.8 <= ratio <= 2.0:
            score += 20
        elif 0.5 <= ratio <= 3.0:
            score += 10
        
        # Growth rate (10 points)
        peer_growth = peer_grok.get('estimated_monthly_follower_growth_percent', 0)
        if peer_growth > 5:
            score += 10
        elif peer_growth > 2:
            score += 5
        
        return min(score, 100)


    def _generate_match_reason(self, user_profile: Dict, peer_profile: Dict) -> str:
        """Generate match reason based on real data"""
        
        user_grok = user_profile.get('grok_profile', {})
        peer_grok = peer_profile.get('grok_profile', {})
        
        peer_followers = peer_profile['basic_metrics']['followers_count']
        user_followers = user_profile['basic_metrics']['followers_count']
        
        follower_diff = ((peer_followers - user_followers) / user_followers * 100) if user_followers > 0 else 0
        
        peer_growth = peer_grok.get('estimated_monthly_follower_growth_percent', 0)
        
        return f"Same niche, {follower_diff:+.0f}% more followers, {peer_growth:.1f}% monthly growth"


    def _generate_growth_edge(self, peer_profile: Dict) -> str:
        """Generate growth edge based on real data"""
        
        grok = peer_profile.get('grok_profile', {})
        
        posts_per_week = grok.get('posting_frequency_per_week', 0)
        visual_ratio = grok.get('visual_content_ratio', 'medium')
        
        return f"Posts {posts_per_week}x/week with {visual_ratio} visual content"
    
    def _get_fully_profiled_peers(self, user_profile: Dict, count: int = 10) -> List[Dict]:
        """
        Get FULLY PROFILED peers from Grok using its built-in knowledge
        """
        grok_profile = user_profile.get('grok_profile', {})
        
        handle = user_profile['handle']
        followers = user_profile['basic_metrics']['followers_count']
        
        # 🔥 FIX: Better follower range - aim for peers at same level or higher
        # For 655 followers: 500 to 2,000 (not 262 to 2,620)
        min_followers = int(followers * 0.8)  # 80% of user's count (slightly below)
        max_followers = int(followers * 3.0)  # 3x user's count (significantly above)
        
        # Ensure minimum floor
        if min_followers < 500:
            min_followers = 500
        
        primary_niche = grok_profile.get('primary_niche', 'general content')
        secondary_topics = json.dumps(grok_profile.get('secondary_topics', []))
        content_style = grok_profile.get('content_style', 'varied')
        language_mix = grok_profile.get('language_mix', 'English 100%')
        
        prompt = f"""You are an expert X/Twitter analyst with knowledge of thousands of accounts.

    Find {count} similar accounts to @{handle} that are GROWING FASTER and are at the SAME LEVEL OR HIGHER.

    USER PROFILE:
    - Handle: @{handle}
    - Followers: {followers:,}
    - Niche: {primary_niche}
    - Topics: {secondary_topics}
    - Content Style: {content_style}
    - Language: {language_mix}

    CRITICAL REQUIREMENTS:
    - Same primary niche + at least 2 overlapping topics
    - Follower count between {min_followers:,} and {max_followers:,} (PREFER accounts with {int(followers * 1.2):,} to {int(followers * 2):,} followers)
    - MUST be growing faster than user (higher monthly growth %)
    - Active accounts (posting 5+/week in 2025)
    - High engagement relative to follower count
    - Global search – no geographic bias

    PRIORITY: Find peers who are slightly ahead (1.2x to 2x followers) and crushing it with growth.

    Return ONLY this JSON ({count} peers with FULL profiles):

    {{
    "peers": [
        {{
        "handle": "exampleuser",
        "followers": 1500,
        "primary_niche": "detailed niche description",
        "secondary_topics": ["topic1", "topic2", "topic3"],
        "content_style": "threads with data, polls, educational",
        "average_likes_per_post": 50,
        "average_views_per_post": 2500,
        "growth_trend_last_30_days": "growing fast",
        "estimated_monthly_growth_percent": 8.0,
        "posting_frequency_per_week": 15,
        "visual_content_ratio": "high",
        "language_mix": "English 100%",
        "match_score": 92,
        "match_reason": "Same niche, 2.3x followers, 3x faster growth",
        "growth_edge": "Posts 3 viral threads/week with data visualizations at 9 AM EST",
        "strengths": ["consistent posting", "high engagement", "data-driven"],
        "weaknesses_for_growth": ["could use more video content"]
        }}
    ]
    }}"""
        
        try:
            response = self.grok.complete_json(
                prompt=prompt,
                temperature=0.0,
                cost_tracker=self.cost_tracker
            )
            
            peers = response.get('peers', [])
            
            if not peers or len(peers) == 0:
                raise ValueError("Grok returned empty peers list")
            
            logger.info(f"✅ Grok returned {len(peers)} fully profiled peer suggestions")
            return peers
            
        except GrokAPIError as e:
            logger.error(f"Grok API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting Grok suggestions: {e}")
            raise
    
    def _format_peers(self, peers: List[Dict]) -> List[Dict]:
        """
        Format Grok's peer data into our standard profile structure
        """
        formatted = []
        
        for peer in peers:
            # Build profile matching our structure
            profile = {
                'handle': peer.get('handle', '').lstrip('@'),
                'user_id': None,  # We don't have this
                'name': peer.get('handle', ''),  # Use handle as name
                'bio': '',
                'profile_image': '',
                'basic_metrics': {
                    'followers_count': peer.get('followers', 0),
                    'following_count': 0,
                    'tweet_count': 0,
                    'listed_count': 0,
                    'follower_following_ratio': 0
                },
                'grok_profile': {
                    'handle': peer.get('handle', ''),
                    'followers': peer.get('followers', 0),
                    'primary_niche': peer.get('primary_niche', ''),
                    'secondary_topics': peer.get('secondary_topics', []),
                    'content_style': peer.get('content_style', ''),
                    'average_likes_per_post': peer.get('average_likes_per_post', 0),
                    'average_views_per_post': peer.get('average_views_per_post', 0),
                    'growth_trend_last_30_days': peer.get('growth_trend_last_30_days', 'unknown'),
                    'estimated_monthly_follower_growth_percent': peer.get('estimated_monthly_growth_percent', 0),
                    'posting_frequency_per_week': peer.get('posting_frequency_per_week', 0),
                    'visual_content_ratio': peer.get('visual_content_ratio', 'medium'),
                    'language_mix': peer.get('language_mix', 'English 100%'),
                    'strengths': peer.get('strengths', []),
                    'weaknesses_for_growth': peer.get('weaknesses_for_growth', [])
                },
                # Legacy fields
                'niche': self._extract_niche(peer.get('primary_niche', '')),
                'content_style': {},
                'posting_rhythm': {'posts_per_week': peer.get('posting_frequency_per_week', 0)},
                'engagement_baseline': {'avg_likes': peer.get('average_likes_per_post', 0)},
                'growth_velocity': {'estimated_30d_growth': 0},
                # Match data
                'match_score': peer.get('match_score', 0),
                'match_reason': peer.get('match_reason', ''),
                'growth_edge': peer.get('growth_edge', ''),
                'growth_advantage': f"+{peer.get('estimated_monthly_growth_percent', 0)}% growth/month"
            }
            
            formatted.append(profile)
        
        # Sort by match score
        formatted.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return formatted
    
    def _extract_niche(self, primary_niche: str) -> str:
        """Extract simple niche category"""
        niche_keywords = {
            'tech': ['technology', 'software', 'developer', 'programming'],
            'business': ['business', 'entrepreneur', 'startup', 'founder'],
            'marketing': ['marketing', 'content', 'seo'],
            'finance': ['finance', 'investing', 'trading', 'stocks', 'crypto'],
        }
        
        primary_lower = primary_niche.lower()
        for niche, keywords in niche_keywords.items():
            if any(kw in primary_lower for kw in keywords):
                return niche
        
        return 'other'
    
    def _save_to_database(self, user_id: str, peers: List[Dict]):
        """Save peer matches to database"""
        try:
            session = get_session()
            
            # Delete old matches
            session.query(PeerMatch).filter_by(user_id=user_id).delete()
            
            # Insert new matches
            for peer in peers:
                match = PeerMatch(
                    user_id=user_id,
                    peer_handle=peer['handle'],
                    peer_followers=peer['basic_metrics']['followers_count'],
                    match_score=peer.get('match_score', 0),
                    match_reason=peer.get('match_reason', '')
                )
                session.add(match)
            
            session.commit()
            session.close()
            
            logger.info(f"✅ Saved {len(peers)} peer matches to database")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            session.rollback()
            session.close()