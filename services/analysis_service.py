# services/analysis_service.py
from typing import Dict, Optional
from datetime import datetime, timedelta
from data.user_profiler import UserProfiler
from ai.peer_matcher import PeerMatcher
from ai.insights_generator import InsightsGenerator
from db.models import User, UserProfile, PeerMatch, Analysis
from db.connection import get_session_direct
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
        """
        session = get_session_direct()
        
        try:
            # Get user
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            logger.info(f"✅ Starting analysis for @{user.x_handle}")
            
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
            logger.info("🔄 Generating insights...")
            analysis_data = self.insights.generate_insights(
                user_profile_data,
                peer_profiles,
                num_insights=3
            )
            
            # STEP 4: Save Analysis
            analysis_record = self._save_analysis(
                user_id,
                user_profile_data,
                peer_profiles,
                analysis_data,
                session
            )
            
            # Build response
            result = {
                'analysis_id': str(analysis_record.id),
                'user_profile': user_profile_data,
                'peer_profiles': peer_profiles,
                'insights': analysis_data,
                'created_at': analysis_record.created_at.isoformat(),
            }
            
            logger.info(f"✅ Analysis complete for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def _get_or_create_user_profile(self, user, session, force_refresh=False):
        """Get cached profile or create new one"""
        
        # Check cache
        if not force_refresh:
            cached = session.query(UserProfile).filter_by(
                user_id=user.id
            ).order_by(UserProfile.analyzed_at.desc()).first()
            
            if cached and cached.expires_at > datetime.utcnow():
                logger.info(f"✅ Using cached profile (expires: {cached.expires_at})")
                return {
                    'db_id': str(cached.id),
                    'handle': user.x_handle,
                    'basic_metrics': {
                        'followers_count': cached.followers_count,
                        'following_count': cached.following_count,
                        'tweet_count': cached.tweet_count,
                    },
                    'grok_profile': cached.grok_profile,
                    'niche': cached.niche,
                    'content_style': cached.content_style or {},
                    'engagement_baseline': {
                        'engagement_rate': cached.avg_engagement_rate,
                    },
                    'growth_velocity': {
                        'estimated_30d_growth': cached.growth_30d,
                    }
                }
        
        # Create new profile
        logger.info("🔄 Creating new user profile...")
        profile_data = self.profiler.analyze_user_from_handle(user.x_handle)
        
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
    
    def _get_or_create_peers(self, user, user_profile_data, session, force_refresh=False):
        """Get cached peers or find new ones"""
        
        # Check cache (24 hour TTL)
        if not force_refresh:
            cached = session.query(PeerMatch).filter(
                PeerMatch.user_id == user.id,
                PeerMatch.expires_at > datetime.utcnow()
            ).order_by(PeerMatch.created_at.desc()).limit(5).all()
            
            if cached and len(cached) >= 5:
                logger.info(f"✅ Using cached peers for @{user.x_handle}")
                return [
                    {
                        'handle': peer.peer_handle,
                        'basic_metrics': {
                            'followers_count': peer.peer_followers,
                        },
                        'grok_profile': peer.peer_profile,
                        'match_score': peer.match_score,
                        'match_reason': peer.match_reason,
                        'growth_edge': peer.growth_edge,
                    }
                    for peer in cached
                ]
        
        # Find new peers
        logger.info("🔄 Finding peer accounts...")
        peer_profiles = self.matcher.find_peers(
            user_profile_data,
            count=5,
            save_to_db=False
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
                match_score=peer.get('match_score', 85),
                match_reason=peer.get('match_reason', ''),
                growth_edge=peer.get('growth_edge', ''),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            session.add(peer_match)
        
        session.commit()
        logger.info(f"✅ Saved {len(peer_profiles)} peers with 24h cache")
        
        return peer_profiles
    
    def _save_analysis(self, user_id, user_profile, peer_profiles, insights_data, session):
        """Save analysis to database"""
        
        analysis = Analysis(
            user_id=user_id,
            insights_data=insights_data,
            created_at=datetime.utcnow()
        )
        session.add(analysis)
        session.commit()
        session.refresh(analysis)
        
        logger.info(f"✅ Analysis saved: {analysis.id}")
        return analysis