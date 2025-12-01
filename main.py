from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.connection import get_session
from db.models import User, UserProfile, Analysis, PeerMatch  # ← Add PeerMatch here
from services.analysis_service import AnalysisService
from auth.twitter_oauth import TwitterOAuth
from typing import Optional
import logging
from datetime import datetime
import secrets
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LevelX API", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for OAuth callback
class OAuthCallbackRequest(BaseModel):
    code: str
    state: str

# Helper: Get current user (for now, just get first user)
def get_current_user_from_session(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session)
):
    """Get current user from session token"""
    
    if not authorization:
        # For development: use first user if no auth header
        user = session.query(User).first()
        if not user:
            raise HTTPException(status_code=401, detail="No user found. Please authenticate.")
        return user
    
    # Extract token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        user_id = token.split(":")[0]
        user = session.query(User).filter_by(id=user_id).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
def root():
    return {
        "message": "LevelX API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

# ============================================
# USER ENDPOINTS
# ============================================

@app.get("/api/user/me")
def get_current_user(
    user: User = Depends(get_current_user_from_session),
    session: Session = Depends(get_session)
):
    """Get current logged-in user"""
    
    # Get latest profile for followers/following info
    profile = session.query(UserProfile).filter_by(user_id=user.id).order_by(UserProfile.analyzed_at.desc()).first()
    
    # Fix: Use x_handle instead of username
    handle = user.x_handle if hasattr(user, 'x_handle') else '@unknown'
    if not handle.startswith('@'):
        handle = f"@{handle}"
    
    return {
        "id": str(user.id),
        "handle": handle,
        "display_name": handle.replace('@', ''),  # Use handle as display name for now
        "avatar_url": None,
        "followers_count": profile.followers_count if profile else 0,
        "following_count": profile.following_count if profile else 0,
        "credits": 250,  # TODO: Implement credits system
    }

@app.get("/api/user/credits")
def get_user_credits(user: User = Depends(get_current_user_from_session)):
    """Get user's credit balance"""
    return {"credits": 250}  # TODO: Implement credits system

# ============================================
# ANALYSIS ENDPOINTS
# ============================================

@app.get("/api/analysis/latest")
def get_latest_analysis(
    user: User = Depends(get_current_user_from_session),
    session: Session = Depends(get_session)
):
    """Get user's most recent analysis"""
    
    analysis = (
        session.query(Analysis)
        .filter_by(user_id=user.id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    
    if not analysis:
        logger.info(f"No analysis found for user {user.id}")
        return None
    
    # Get user profile
    profile = (
        session.query(UserProfile)
        .filter_by(user_id=user.id)
        .order_by(UserProfile.analyzed_at.desc())
        .first()
    )
    
    # Get ONLY the most recent batch of peers (same timestamp as analysis)
    peers = (
        session.query(PeerMatch)
        .filter(
            PeerMatch.user_id == user.id,
            PeerMatch.created_at >= analysis.created_at - timedelta(minutes=5)  # Within 5 min of analysis
        )
        .order_by(PeerMatch.match_score.desc())
        .limit(5)
        .all()
    )
    
    logger.info(f"Found {len(peers)} peers from latest analysis batch")
    
    if not profile:
        logger.warning(f"No profile found for user {user.id}")
        return None
    
    grok_profile = profile.grok_profile or {}
    
    # 🔥 FIX: Build proper response with peers
    result = {
        "analysis_id": str(analysis.id),
        "created_at": analysis.created_at.isoformat(),
        "user_profile": {
            "handle": user.x_handle,
            "avg_engagement_rate": profile.avg_engagement_rate or 0,
            "growth_30d": profile.growth_30d or 0,
            "posting_frequency_per_week": grok_profile.get('posting_frequency_per_week', 0),
            "viral_index": 0,
            "content_quality_score": 0,
            "niche_authority_score": 0,
            "posting_consistency": grok_profile.get('posting_consistency', 0),
        },
        # 🔥 FIX: Add peer_profiles with actual data
        "peer_profiles": [
            {
                "handle": peer.peer_handle,
                "name": peer.peer_profile.get('name', peer.peer_handle.replace('@', '')) if peer.peer_profile else peer.peer_handle.replace('@', ''),
                "profile_image": peer.peer_profile.get('profile_image') if peer.peer_profile else None,
                "basic_metrics": {
                    "followers_count": peer.peer_followers,
                },
                "grok_profile": peer.peer_profile,
                "match_score": peer.match_score,
                "match_reason": peer.match_reason,
                "growth_edge": peer.growth_edge,
            }
            for peer in peers
        ],
        "insights": analysis.insights if hasattr(analysis, 'insights') and analysis.insights else [],
        "growth_score": analysis.growth_score or 0,
        "percentile": 0,
        "credits_used": 15,
    }
    
    logger.info(f"Returning latest analysis for user {user.id} with {len(peers)} peers")
    return result

@app.post("/api/analysis/run")
def run_analysis(
    user: User = Depends(get_current_user_from_session),
    session: Session = Depends(get_session)
):
    """Run new analysis for user"""
    
    logger.info(f"Starting analysis for user {user.id} (@{user.x_handle if hasattr(user, 'x_handle') else 'unknown'})")
    
    try:
        # Initialize analysis service
        service = AnalysisService()
        
        # Run full analysis
        result = service.run_full_analysis(
            user_id=str(user.id),
            force_refresh_profile=False,
            force_refresh_peers=False
        )
        
        logger.info(f"Analysis complete for user {user.id}")
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed for user {user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/analysis/history")
def get_analysis_history(
    limit: int = 5,
    user: User = Depends(get_current_user_from_session),
    session: Session = Depends(get_session)
):
    """Get user's analysis history"""
    
    analyses = (
        session.query(Analysis)
        .filter_by(user_id=user.id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .all()
    )
    
    result = []
    for a in analyses:
        # Get profile for this analysis to calculate X-Score
        profile = (
            session.query(UserProfile)
            .filter_by(user_id=user.id)
            .filter(UserProfile.analyzed_at <= a.created_at)
            .order_by(UserProfile.analyzed_at.desc())
            .first()
        )
        
        # Calculate X-Score
        x_score = 0
        if profile:
            grok_profile = profile.grok_profile or {}
            engagement = profile.avg_engagement_rate or 0
            growth = profile.growth_30d or 0
            consistency = grok_profile.get('posting_consistency', 0)
            
            x_score = (
                engagement * 100 * 0.3 +
                growth * 0.4 +
                consistency * 100 * 0.3
            )
            x_score = min(round(x_score * 10) / 10, 100)
        
        result.append({
            "id": str(a.id),
            "created_at": a.created_at.isoformat(),
            "x_score": x_score,
            "credits_used": 15,
        })
    
    return result

@app.get("/api/analysis/{analysis_id}")
def get_analysis_by_id(
    analysis_id: str,
    user: User = Depends(get_current_user_from_session),
    session: Session = Depends(get_session)
):
    """Get specific analysis by ID"""
    
    analysis = (
        session.query(Analysis)
        .filter_by(id=analysis_id, user_id=user.id)
        .first()
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    profile = (
        session.query(UserProfile)
        .filter_by(user_id=user.id)
        .order_by(UserProfile.analyzed_at.desc())
        .first()
    )
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    grok_profile = profile.grok_profile or {}
    
    return {
        "id": str(analysis.id),
        "analyzed_at": analysis.created_at.isoformat(),
        "user_profile": {
            "avg_engagement_rate": profile.avg_engagement_rate or 0,
            "growth_30d": profile.growth_30d or 0,
            "posting_frequency_per_week": grok_profile.get('posting_frequency_per_week', 0),
            "viral_index": 0,
            "content_quality_score": 0,
            "niche_authority_score": 0,
            "posting_consistency": grok_profile.get('posting_consistency', 0),
        },
        "peer_averages": {
            "avg_engagement_rate": 0,
            "growth_30d": 0,
            "posting_frequency_per_week": 0,
            "viral_index": 0,
            "content_quality_score": 0,
            "niche_authority_score": 0,
        },
        "peers": [],
        "insights": [],
        "score_change": 0,
        "percentile": 0,
        "credits_used": 15,
    }

# ============================================
# OAUTH ENDPOINTS
# ============================================

@app.get("/api/auth/login")
def oauth_login():
    """Initiate OAuth flow - returns authorization URL"""
    try:
        oauth = TwitterOAuth()
        auth_url = oauth.get_authorization_url()
        return {"authorization_url": auth_url}
    except Exception as e:
        logger.error(f"OAuth init error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth")


@app.post("/api/auth/callback")
def oauth_callback(
    request: OAuthCallbackRequest,
    session: Session = Depends(get_session)
):
    """Handle OAuth callback"""
    try:
        oauth = TwitterOAuth()
        
        # Exchange code for access token
        token_data = oauth.get_access_token(request.code, request.state)
        if not token_data:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        
        # Get user info from X
        user_info = oauth.get_user_info(access_token)
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        # Check if user exists
        user = session.query(User).filter_by(x_user_id=user_info['id']).first()
        
        if user:
            # Update existing user
            user.x_handle = user_info['username']
            user.oauth_token = access_token
            user.oauth_token_secret = refresh_token
            logger.info(f"Updated existing user: @{user_info['username']}")
        else:
            # Create new user
            user = User(
                id=uuid.uuid4(),
                x_handle=user_info['username'],
                x_user_id=user_info['id'],
                oauth_token=access_token,
                oauth_token_secret=refresh_token,
                subscription_tier='free'
            )
            session.add(user)
            logger.info(f"Created new user: @{user_info['username']}")
        
        session.commit()
        session.refresh(user)
        
        # Generate session token
        session_token = f"{user.id}:{secrets.token_urlsafe(32)}"
        
        return {
            "success": True,
            "token": session_token,
            "user": {
                "id": str(user.id),
                "handle": f"@{user.x_handle}",
                "x_user_id": user.x_user_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@app.post("/api/auth/logout")
def logout():
    """Logout user"""
    return {"success": True, "message": "Logged out successfully"}

# ============================================
# DEVELOPMENT HELPERS
# ============================================

@app.get("/api/debug/users")
def debug_list_users(session: Session = Depends(get_session)):
    """Debug endpoint: List all users"""
    users = session.query(User).all()
    return [
        {
            "id": str(u.id),
            "x_handle": u.x_handle if hasattr(u, 'x_handle') else 'N/A',
            "x_user_id": u.x_user_id if hasattr(u, 'x_user_id') else 'N/A',
        }
        for u in users
    ]

@app.get("/api/debug/analyses")
def debug_list_analyses(session: Session = Depends(get_session)):
    """Debug endpoint: List all analyses"""
    analyses = session.query(Analysis).order_by(Analysis.created_at.desc()).limit(10).all()
    return [
        {
            "id": str(a.id),
            "user_id": str(a.user_id),
            "created_at": a.created_at.isoformat(),
            "has_data": True,
        }
        for a in analyses
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)