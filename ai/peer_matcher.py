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
        save_to_db: bool = False,
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Find similar accounts using Grok AI's built-in knowledge
        
        NO MORE: Fetching tweets, validating accounts, profiling peers
        NOW: Single Grok call returns fully profiled peers!
        """
        logger.info(f"Finding {count} peers for @{user_profile['handle']} using Grok")
        
        try:
            # Single Grok call gets FULLY PROFILED peers
            peers = self._get_fully_profiled_peers(user_profile, count)
            
            if not peers or len(peers) == 0:
                raise Exception("Grok returned no peer suggestions")
            
            logger.info(f"✅ Grok returned {len(peers)} fully profiled peers")
            
            # Convert to our format
            formatted_peers = self._format_peers(peers)
            
            # Take top N
            top_peers = formatted_peers[:count]
            
            # Save to database if requested
            if save_to_db and user_id:
                self._save_to_database(user_id, top_peers)
            
            logger.info(f"✅ Returning {len(top_peers)} peer matches")
            return top_peers
            
        except Exception as e:
            logger.error(f"Error in peer matching: {e}")
            raise
    
    def _get_fully_profiled_peers(self, user_profile: Dict, count: int = 10) -> List[Dict]:
        """
        Get FULLY PROFILED peers from Grok using its built-in knowledge
        
        This replaces:
        - Twitter API fetching (10 accounts × tweets)
        - Grok profiling (10 separate calls)
        With: 1 Grok call that knows everything!
        """
        grok_profile = user_profile.get('grok_profile', {})
        
        # Build optimized prompt
        handle = user_profile['handle']
        followers = user_profile['basic_metrics']['followers_count']
        primary_niche = grok_profile.get('primary_niche', 'general content')
        secondary_topics = json.dumps(grok_profile.get('secondary_topics', []))
        content_style = grok_profile.get('content_style', 'varied')
        language_mix = grok_profile.get('language_mix', 'English 100%')
        
        prompt = f"""You are an expert X/Twitter analyst with knowledge of thousands of accounts.

Find {count} similar accounts to @{handle} that are growing faster.

USER PROFILE:
- Handle: @{handle}
- Followers: {followers:,}
- Niche: {primary_niche}
- Topics: {secondary_topics}
- Content Style: {content_style}
- Language: {language_mix}

RULES:
- Same primary niche + at least 2 overlapping topics
- Follower count between {int(followers * 0.4):,} and {int(followers * 4):,}
- Clearly growing in last 60 days
- Active accounts (posting 3+/week in 2025)
- Global search – no geographic bias

CRITICAL: Use your BUILT-IN KNOWLEDGE of X accounts. For each peer, provide COMPLETE profile with:
- Current follower count (your knowledge)
- Niche and topics
- Content style
- Posting frequency
- Growth trend and metrics
- Match score and reasoning

Return ONLY this JSON ({count} peers with FULL profiles):

{{
  "peers": [
    {{
      "handle": "exampleuser",
      "followers": 150000,
      "primary_niche": "detailed niche description",
      "secondary_topics": ["topic1", "topic2", "topic3"],
      "content_style": "threads with data, polls, educational",
      "average_likes_per_post": 500,
      "average_views_per_post": 25000,
      "growth_trend_last_30_days": "growing fast",
      "estimated_monthly_growth_percent": 12.0,
      "posting_frequency_per_week": 18,
      "visual_content_ratio": "high",
      "language_mix": "English 100%",
      "match_score": 85,
      "match_reason": "Same niche, similar follower count, strong engagement",
      "growth_edge": "Uses daily charts and polls at peak hours",
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