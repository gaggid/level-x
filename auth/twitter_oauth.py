import requests
from urllib.parse import urlencode
import secrets
import hashlib
import base64
from config.settings import settings
from typing import Dict, Optional
from db.models import OAuthState
from db.connection import get_session
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TwitterOAuth:
    def __init__(self):
        self.client_id = settings.X_CLIENT_ID
        self.client_secret = settings.X_CLIENT_SECRET
        self.redirect_uri = settings.X_REDIRECT_URI
        self.authorization_endpoint = "https://twitter.com/i/oauth2/authorize"
        self.token_endpoint = "https://api.twitter.com/2/oauth2/token"
        self.user_endpoint = "https://api.twitter.com/2/users/me"
    
    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier"""
        return secrets.token_urlsafe(32)
    
    def _generate_code_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge from verifier"""
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip('=')
    
    def _store_oauth_state(self, state: str, code_verifier: str):
        """Store OAuth state in database"""
        try:
            session = get_session()
            
            # Clean up old states (older than 10 minutes)
            old_threshold = datetime.utcnow() - timedelta(minutes=10)
            session.query(OAuthState).filter(
                OAuthState.created_at < old_threshold
            ).delete()
            
            # Store new state
            oauth_state = OAuthState(
                state=state,
                code_verifier=code_verifier
            )
            session.add(oauth_state)
            session.commit()
            session.close()
            
            logger.info("OAuth state stored in database")
            
        except Exception as e:
            logger.error(f"Error storing OAuth state: {e}")
            session.rollback()
            session.close()
    
    def _get_oauth_state(self, state: str) -> Optional[str]:
        """Retrieve and delete OAuth state from database"""
        try:
            session = get_session()
            
            oauth_state = session.query(OAuthState).filter_by(state=state).first()
            
            if oauth_state:
                code_verifier = oauth_state.code_verifier
                session.delete(oauth_state)  # Delete after use
                session.commit()
                session.close()
                logger.info("OAuth state retrieved and deleted")
                return code_verifier
            
            session.close()
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving OAuth state: {e}")
            session.close()
            return None
    
    def get_authorization_url(self) -> str:
        """
        Generate OAuth authorization URL with PKCE
        Returns: authorization_url
        """
        # Generate PKCE parameters
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store in database
        self._store_oauth_state(state, code_verifier)
        
        # Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'tweet.read users.read follows.read offline.access',
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        authorization_url = f"{self.authorization_endpoint}?{urlencode(params)}"
        
        logger.info("Generated authorization URL")
        return authorization_url
    
    def get_access_token(self, code: str, state: str) -> Optional[Dict]:
        """
        Exchange authorization code for access token
        """
        try:
            # Retrieve code_verifier from database
            code_verifier = self._get_oauth_state(state)
            
            if not code_verifier:
                logger.error("OAuth state not found or expired")
                return None
            
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri,
                'code_verifier': code_verifier,
                'client_id': self.client_id
            }
            
            response = requests.post(
                self.token_endpoint,
                data=data,
                auth=(self.client_id, self.client_secret)
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("Successfully obtained access token")
            return token_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting access token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Fetch user profile from X API
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            params = {
                'user.fields': 'id,name,username,profile_image_url,public_metrics,description'
            }
            
            response = requests.get(
                self.user_endpoint,
                headers=headers,
                params=params
            )
            
            response.raise_for_status()
            user_data = response.json()
            
            logger.info(f"Successfully fetched user info for @{user_data['data']['username']}")
            return user_data['data']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user info: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """
        Refresh access token using refresh token
        """
        try:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id
            }
            
            response = requests.post(
                self.token_endpoint,
                data=data,
                auth=(self.client_id, self.client_secret)
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("Successfully refreshed access token")
            return token_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing token: {e}")
            return None