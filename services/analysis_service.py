# services/analysis_service.py
from typing import Dict, Optional
from datetime import datetime, timedelta
from data.user_profiler import UserProfiler
from ai.peer_matcher import PeerMatcher
from ai.insights_generator import InsightsGenerator
from db.models import User, UserProfile, PeerMatch, Analysis
from db.connection import get_session_direct
import logging
from ai.peer_insights_generator import PeerInsightsGenerator  # 🔥 ADD THIS

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Orchestrates full analysis with caching and database persistence
    """
    
    def __init__(self, cost_tracker=None):
        self.profiler = UserProfiler(cost_tracker)
        self.matcher = PeerMatcher(cost_tracker)
        self.insights = InsightsGenerator(cost_tracker)
        self.peer_insights = PeerInsightsGenerator(cost_tracker)  # 🔥 NEW
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
            
            # STEP 2.5: 🔥 NEW - Generate Individual Peer Insights
            logger.info("🔄 Generating individual peer insights...")
            for peer in peer_profiles:
                try:
                    peer_analysis = self.peer_insights.analyze_peer(
                        user_profile_data,
                        peer,
                        fetch_tweets=True  # Fetch example tweets
                    )
                    peer['peer_insights'] = peer_analysis
                    logger.info(f"✅ Analyzed @{peer['handle']}")
                except Exception as e:
                    logger.warning(f"Could not analyze peer @{peer['handle']}: {e}")
                    peer['peer_insights'] = None
            
            # STEP 3: Generate Overall Insights (always fresh)
            logger.info("🔄 Generating overall insights...")
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
            
            # STEP 5: Build response with peer insights
            result = {
                'analysis_id': str(analysis_record.id),
                'user_profile': user_profile_data,
                'peer_profiles': [
                    {
                        'handle': peer.get('handle'),
                        'name': peer.get('name'),
                        'profile_image': peer.get('profile_image'),
                        'basic_metrics': peer.get('basic_metrics'),
                        'grok_profile': peer.get('grok_profile'),
                        'match_score': peer.get('match_score'),
                        'match_reason': peer.get('match_reason'),
                        'growth_edge': peer.get('growth_edge'),
                        'peer_insights': peer.get('peer_insights'),  # 🔥 NEW
                    }
                    for peer in peer_profiles
                ],
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
        """
        Always get fresh peers, but track history to avoid repetition
        """
        
        # Get previously analyzed peers to avoid repeating
        previous_peers = session.query(PeerMatch).filter_by(
            user_id=user.id
        ).order_by(PeerMatch.created_at.desc()).limit(20).all()
        
        # Extract handles of previously analyzed peers
        excluded_handles = set([p.peer_handle.lower() for p in previous_peers])
        
        logger.info(f"🔄 Finding NEW peer accounts (excluding {len(excluded_handles)} previous peers)...")
        
        # Find new peers (excluding previously analyzed ones)
        peer_profiles = self.matcher.find_peers(
            user_profile_data,
            count=5,
            excluded_handles=excluded_handles,  # Pass excluded handles
            save_to_db=False
        )
        
        if not peer_profiles or len(peer_profiles) == 0:
            logger.warning("No new peers found, allowing repeats...")
            # If we can't find new peers, allow repeats
            peer_profiles = self.matcher.find_peers(
                user_profile_data,
                count=5,
                excluded_handles=set(),  # No exclusions
                save_to_db=False
            )
        
        # Archive old peer matches (don't delete, keep for history)
        # We'll keep them but they won't be used in new analysis
        logger.info(f"Keeping {len(previous_peers)} previous peers in history")
        
        # Save new peers with timestamp
        for peer in peer_profiles:
            peer_match = PeerMatch(
                user_id=user.id,
                peer_handle=peer['handle'],
                peer_followers=peer['basic_metrics']['followers_count'],
                peer_profile=peer['grok_profile'],
                peer_insights=peer.get('peer_insights'),
                example_tweets=peer.get('peer_insights', {}).get('example_tweets', []) if peer.get('peer_insights') else [],
                match_score=peer.get('match_score', 85),
                match_reason=peer.get('match_reason', ''),
                growth_edge=peer.get('growth_edge', ''),
                created_at=datetime.utcnow(),  # Fresh timestamp
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            session.add(peer_match)
        
        session.commit()
        logger.info(f"✅ Saved {len(peer_profiles)} NEW peers")
        
        return peer_profiles
    
    def _save_analysis(self, user_id, user_profile, peer_profiles, insights_data, session):
        """Save analysis to database"""
        
        # Calculate growth score from user profile
        growth_score = 0.0
        if 'grok_profile' in user_profile:
            grok = user_profile['grok_profile']
            growth_score = grok.get('estimated_monthly_follower_growth_percent', 0)
        
        # Create analysis record
        analysis = Analysis(
            user_id=user_id,
            user_profile_id=user_profile.get('db_id'),
            growth_score=growth_score,
            insights=insights_data,  # ← FIXED
            comparison_data={
                'peer_count': len(peer_profiles),
                'peers': [p.get('handle') for p in peer_profiles]
            },
            created_at=datetime.utcnow()
        )
        
        session.add(analysis)
        session.commit()
        session.refresh(analysis)
        
        logger.info(f"✅ Analysis saved with ID: {analysis.id}")
        return analysis