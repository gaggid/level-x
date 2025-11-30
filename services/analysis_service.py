# services/analysis_service.py
from typing import Dict, Optional
from datetime import datetime, timedelta
from data.user_profiler import UserProfiler
from ai.peer_matcher import PeerMatcher
from ai.insights_generator import InsightsGenerator
from db.models import User, UserProfile, PeerMatch, Analysis
from db.connection import get_session
import logging

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Orchestrates full analysis with caching and database persistence
    """
    
    def __init__(self, cost_tracker=None):
        self.profiler = UserProfiler(cost_tracker)
        self.matcher = PeerMatcher(cost_tracker)
        self.insights = InsightsGenerator(cost_tracker)
        self.cost_tracker = cost_tracker
    
    def run_full_analysis(
        self,
        user_id: str,
        force_refresh_profile: bool = False,
        force_refresh_peers: bool = False
    ) -> Dict:
        """
        Run complete analysis with smart caching
        
        Args:
            user_id: UUID of user
            force_refresh_profile: Skip cache, re-profile user
            force_refresh_peers: Skip cache, find new peers
        
        Returns:
            Complete analysis dict
        """
        session = get_session()
        
        try:
            # Get user
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # STEP 1: Get/Create User Profile
            user_profile_data = self._get_or_create_user_profile(
                user, 
                session,
                force_refresh=force_refresh_profile
            )
            
            # STEP 2: Get/Create Peer Matches
            peer_profiles = self._get_or_create_peers(
                user,
                user_profile_data,
                session,
                force_refresh=force_refresh_peers
            )
            
            # STEP 3: Generate Insights (always fresh)
            analysis_data = self.insights.generate_insights(
                user_profile_data,
                peer_profiles,
                num_insights=3
            )
            
            # STEP 4: Save Analysis to Database
            analysis = Analysis(
                user_id=user_id,
                user_profile_id=user_profile_data.get('db_id'),
                growth_score=analysis_data.get('growth_score', 0),
                insights=analysis_data.get('insights', []),
                comparison_data=analysis_data.get('comparison_data', {})
            )
            session.add(analysis)
            session.commit()
            
            logger.info(f"✅ Full analysis complete for @{user.x_handle}")
            
            # Return everything
            return {
                'user_profile': user_profile_data,
                'peers': peer_profiles,
                'analysis': analysis_data,
                'analysis_id': str(analysis.id),
                'created_at': analysis.created_at
            }
            
        finally:
            session.close()
    
    def _get_or_create_user_profile(
        self,
        user: User,
        session,
        force_refresh: bool = False
    ) -> Dict:
        """
        Get user profile from cache or create new one
        """
        # Check cache (6 hour TTL)
        if not force_refresh:
            cached = session.query(UserProfile).filter(
                UserProfile.user_id == user.id,
                UserProfile.expires_at > datetime.utcnow()
            ).order_by(UserProfile.analyzed_at.desc()).first()
            
            if cached:
                logger.info(f"✅ Using cached profile for @{user.x_handle}")
                # Reconstruct FULL profile from cached data
                profile_data = {
                    'handle': user.x_handle,
                    'user_id': str(user.x_user_id),
                    'name': user.x_handle,
                    'bio': '',
                    'profile_image': '',
                    'basic_metrics': {
                        'followers_count': cached.followers_count or 0,
                        'following_count': cached.following_count or 0,
                        'tweet_count': cached.tweet_count or 0,
                        'listed_count': 0,
                        'follower_following_ratio': 0
                    },
                    'grok_profile': cached.grok_profile or {},
                    'niche': cached.niche or 'other',
                    'content_style': cached.content_style or {},
                    'posting_rhythm': {'posts_per_week': 0},
                    'engagement_baseline': {'engagement_rate': cached.avg_engagement_rate or 0},
                    'growth_velocity': {'estimated_30d_growth': cached.growth_30d or 0},
                    'db_id': str(cached.id)
                }
                return profile_data
        
        # Create new profile
        logger.info(f"🔄 Creating new profile for @{user.x_handle}")
        
        # Fetch from Twitter + Grok
        from data.twitter_client import TwitterAPIClient
        twitter = TwitterAPIClient(self.cost_tracker)
        
        user_data = twitter.get_user_by_handle(user.x_handle)
        
        # Smart tweet fetching
        followers = user_data.get('public_metrics', {}).get('followers_count', 0)
        needs_tweets = self.profiler._should_fetch_tweets(followers)
        
        if needs_tweets:
            tweets = twitter.get_user_tweets(user.x_handle, max_results=40)
        else:
            tweets = None
        
        profile_data = self.profiler.analyze_user(user_data, tweets)
        
        # Save to database
        user_profile = UserProfile(
            user_id=user.id,
            followers_count=profile_data['basic_metrics']['followers_count'],
            following_count=profile_data['basic_metrics']['following_count'],
            tweet_count=profile_data['basic_metrics'].get('tweet_count', 0),
            grok_profile=profile_data['grok_profile'],
            niche=profile_data['niche'],
            content_style=profile_data.get('content_style', {}),
            avg_engagement_rate=profile_data['engagement_baseline']['engagement_rate'],
            growth_30d=profile_data['growth_velocity']['estimated_30d_growth'],
            analyzed_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=6)
        )
        session.add(user_profile)
        session.commit()
        session.refresh(user_profile)
        
        profile_data['db_id'] = str(user_profile.id)
        logger.info(f"✅ Profile saved with 6h cache")
        
        return profile_data
    
    def _get_or_create_peers(
        self,
        user: User,
        user_profile_data: Dict,
        session,
        force_refresh: bool = False
    ) -> list:
        """
        Get peer matches from cache or create new ones
        """
        # Check cache (24 hour TTL)
        if not force_refresh:
            cached = session.query(PeerMatch).filter(
                PeerMatch.user_id == user.id,
                PeerMatch.expires_at > datetime.utcnow()
            ).order_by(PeerMatch.created_at.desc()).limit(5).all()
            
            if cached and len(cached) >= 5:
                logger.info(f"✅ Using cached peers for @{user.x_handle}")
                return [peer.peer_profile for peer in cached]
        
        # Find new peers
        logger.info(f"🔄 Finding new peers for @{user.x_handle}")
        
        peer_profiles = self.matcher.find_peers(
            user_profile_data,
            count=5,
            save_to_db=False  # We'll save with our own logic
        )
        
        # Delete old peers
        session.query(PeerMatch).filter_by(user_id=user.id).delete()
        
        # Save new peers
        for peer in peer_profiles:
            peer_match = PeerMatch(
                user_id=user.id,
                peer_handle=peer['handle'],
                peer_followers=peer['basic_metrics']['followers_count'],
                peer_profile=peer['grok_profile'],
                match_score=peer.get('match_score', 0),
                match_reason=peer.get('match_reason', ''),
                growth_edge=peer.get('growth_edge', ''),
                expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour cache
            )
            session.add(peer_match)
        
        session.commit()
        logger.info(f"✅ Peers saved with 24h cache")
        
        return peer_profiles
    
    def force_refresh_peers_only(self, user_id: str) -> Dict:
        """
        Re-run peer matching without re-profiling user
        (Ad-hoc use case you mentioned)
        """
        return self.run_full_analysis(
            user_id,
            force_refresh_profile=False,  # Keep cached profile
            force_refresh_peers=True       # Get new peers
        )