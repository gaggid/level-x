# C:\Python\levelx\main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from db.connection import get_session
from db.models import User, UserProfile, Analysis
from services.analysis_service import AnalysisService
from typing import Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LevelX API", version="1.0.0")

# CORS for frontend
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

# Helper: Get current user (for now, just get first user)
def get_current_user_from_session(session: Session = Depends(get_session)):
    user = session.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found. Please authenticate first.")
    return user

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
    
    # Fix: Use created_at instead of analyzed_at for Analysis
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
    
    # Build response from analysis data
    result = {
        "id": str(analysis.id),
        "analyzed_at": analysis.created_at.isoformat(),
        "user_profile": {
            "avg_engagement_rate": profile.avg_engagement_rate if profile else 0.045,
            "growth_30d": profile.growth_30d if profile else 8.5,
            "posting_frequency_per_week": 12,
            "viral_index": 65,
            "content_quality_score": 80,
            "niche_authority_score": 70,
            "posting_consistency": 0.85,
        },
        "peer_averages": {
            "avg_engagement_rate": 0.052,
            "growth_30d": 12.3,
            "posting_frequency_per_week": 15,
            "viral_index": 78,
            "content_quality_score": 75,
            "niche_authority_score": 80,
        },
        "peers": analysis.peer_profiles if hasattr(analysis, 'peer_profiles') else [],
        "insights": analysis.insights if hasattr(analysis, 'insights') else [],
        "score_change": 2.4,
        "percentile": 68,
        "credits_used": 15,
    }
    
    logger.info(f"Returning latest analysis for user {user.id}")
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
    
    # Fix: Use created_at instead of analyzed_at
    analyses = (
        session.query(Analysis)
        .filter_by(user_id=user.id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return [
        {
            "id": str(a.id),
            "created_at": a.created_at.isoformat(),
            "x_score": 84.5,  # TODO: Calculate from analysis data
            "credits_used": 15,
        }
        for a in analyses
    ]

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
    
    return {
        "id": str(analysis.id),
        "analyzed_at": analysis.created_at.isoformat(),
        "user_profile": {
            "avg_engagement_rate": profile.avg_engagement_rate if profile else 0,
            "growth_30d": profile.growth_30d if profile else 0,
            "posting_frequency_per_week": 12,
            "viral_index": 65,
            "content_quality_score": 80,
            "niche_authority_score": 70,
            "posting_consistency": 0.85,
        },
        "peer_averages": {
            "avg_engagement_rate": 0.052,
            "growth_30d": 12.3,
            "posting_frequency_per_week": 15,
            "viral_index": 78,
            "content_quality_score": 75,
            "niche_authority_score": 80,
        },
        "peers": analysis.peer_profiles if hasattr(analysis, 'peer_profiles') else [],
        "insights": analysis.insights if hasattr(analysis, 'insights') else [],
        "score_change": 2.4,
        "percentile": 68,
        "credits_used": 15,
    }

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