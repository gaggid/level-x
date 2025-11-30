import streamlit as st
from db.models import User
from db.connection import get_session
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    
    @staticmethod
    def create_user(x_user_data: dict, oauth_token: str, oauth_refresh_token: str = None) -> Optional[User]:
        """
        Create or update user in database
        """
        try:
            session = get_session()
            
            # Check if user already exists
            user = session.query(User).filter_by(
                x_user_id=x_user_data['id']
            ).first()
            
            if user:
                # Update existing user
                user.x_handle = x_user_data['username']
                user.oauth_token = oauth_token
                user.oauth_token_secret = oauth_refresh_token
                logger.info(f"Updated existing user @{user.x_handle}")
            else:
                # Create new user
                user = User(
                    x_handle=x_user_data['username'],
                    x_user_id=x_user_data['id'],
                    oauth_token=oauth_token,
                    oauth_token_secret=oauth_refresh_token,
                    subscription_tier='free'
                )
                session.add(user)
                logger.info(f"Created new user @{user.x_handle}")
            
            session.commit()
            session.refresh(user)
            session.close()
            
            return user
            
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            session.rollback()
            session.close()
            return None
    
    @staticmethod
    def set_user_session(user: User, x_user_data: dict):
        """
        Store user in Streamlit session state
        """
        st.session_state['user'] = {
            'id': str(user.id),
            'x_handle': user.x_handle,
            'x_user_id': user.x_user_id,
            'x_name': x_user_data.get('name', ''),
            'x_profile_image': x_user_data.get('profile_image_url', ''),
            'followers_count': x_user_data.get('public_metrics', {}).get('followers_count', 0),
            'subscription_tier': user.subscription_tier,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
        logger.info(f"User session created for @{user.x_handle}")
    
    @staticmethod
    def get_current_user() -> Optional[dict]:
        """
        Get current user from session
        """
        return st.session_state.get('user', None)
    
    @staticmethod
    def is_authenticated() -> bool:
        """
        Check if user is authenticated
        """
        return 'user' in st.session_state and st.session_state['user'] is not None
    
    @staticmethod
    def logout():
        """
        Clear user session
        """
        if 'user' in st.session_state:
            logger.info(f"User @{st.session_state['user']['x_handle']} logged out")
            del st.session_state['user']
        
        # Clear OAuth state
        if 'oauth_state' in st.session_state:
            del st.session_state['oauth_state']
        if 'code_verifier' in st.session_state:
            del st.session_state['code_verifier']