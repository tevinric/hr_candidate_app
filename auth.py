import msal
import streamlit as st
import requests
import logging
from typing import Optional, Dict, Any
from config import Config
import os

class AuthManager:
    """Microsoft Entra authentication manager"""
    
    def __init__(self):
        # Azure AD configuration
        self.client_id = os.environ.get('AZURE_AD_CLIENT_ID', '')
        self.client_secret = os.environ.get('AZURE_AD_CLIENT_SECRET', '')
        self.tenant_id = os.environ.get('AZURE_AD_TENANT_ID', '')
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.authorized_group_id = os.environ.get('AZURE_AD_AUTHORIZED_GROUP_ID', '')
        
        # Redirect URI (must match Azure app registration)
        self.redirect_uri = os.environ.get('AZURE_AD_REDIRECT_URI', 'http://localhost:8501')
        
        # Scopes
        self.scopes = [
            "User.Read",
            "GroupMember.Read.All"
        ]
        
        # Initialize MSAL app
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
        
        logging.info("AuthManager initialized")
    
    def is_configured(self) -> bool:
        """Check if authentication is properly configured"""
        required_vars = [
            self.client_id,
            self.client_secret, 
            self.tenant_id,
            self.authorized_group_id
        ]
        return all(var for var in required_vars)
    
    def get_auth_url(self) -> str:
        """Get the authorization URL for Microsoft login"""
        try:
            auth_url = self.app.get_authorization_request_url(
                scopes=self.scopes,
                redirect_uri=self.redirect_uri,
                state=st.session_state.get('auth_state', 'default_state')
            )
            logging.info("Generated auth URL successfully")
            return auth_url
        except Exception as e:
            logging.error(f"Error generating auth URL: {str(e)}")
            return ""
    
    def handle_auth_callback(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """Handle authentication callback and get user info"""
        try:
            # Get token using authorization code
            result = self.app.acquire_token_by_authorization_code(
                code=auth_code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if "access_token" in result:
                # Get user information
                user_info = self.get_user_info(result["access_token"])
                if user_info:
                    # Check group membership
                    is_authorized = self.check_group_membership(
                        result["access_token"], 
                        user_info.get("id")
                    )
                    
                    user_info["is_authorized"] = is_authorized
                    user_info["access_token"] = result["access_token"]
                    
                    logging.info(f"Authentication successful for user: {user_info.get('mail', user_info.get('userPrincipalName'))}")
                    return user_info
                else:
                    logging.error("Failed to get user information")
            else:
                logging.error(f"Authentication failed: {result.get('error_description', 'Unknown error')}")
                
        except Exception as e:
            logging.error(f"Error in auth callback: {str(e)}")
        
        return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Microsoft Graph API"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "id": user_data.get("id"),
                    "name": user_data.get("displayName"),
                    "email": user_data.get("mail") or user_data.get("userPrincipalName"),
                    "given_name": user_data.get("givenName"),
                    "surname": user_data.get("surname"),
                    "job_title": user_data.get("jobTitle"),
                    "department": user_data.get("department")
                }
            else:
                logging.error(f"Failed to get user info: {response.status_code} - {response.text}")
                
        except Exception as e:
            logging.error(f"Error getting user info: {str(e)}")
        
        return None
    
    def check_group_membership(self, access_token: str, user_id: str) -> bool:
        """Check if user is member of authorized group"""
        if not self.authorized_group_id:
            logging.warning("No authorized group ID configured, allowing access")
            return True
        
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Check if user is member of the specific group
            response = requests.get(
                f'https://graph.microsoft.com/v1.0/groups/{self.authorized_group_id}/members',
                headers=headers
            )
            
            if response.status_code == 200:
                members = response.json().get("value", [])
                user_ids = [member.get("id") for member in members]
                is_member = user_id in user_ids
                
                logging.info(f"Group membership check: User {user_id} is {'authorized' if is_member else 'not authorized'}")
                return is_member
            else:
                logging.error(f"Failed to check group membership: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error checking group membership: {str(e)}")
            return False
    
    def logout(self):
        """Clear authentication session"""
        # Clear Streamlit session state
        auth_keys = [key for key in st.session_state.keys() if key.startswith('auth_')]
        for key in auth_keys:
            del st.session_state[key]
        
        # Clear user session
        if 'user_info' in st.session_state:
            del st.session_state['user_info']
        if 'authenticated' in st.session_state:
            del st.session_state['authenticated']
        
        logging.info("User logged out")
    
    def get_logout_url(self) -> str:
        """Get Microsoft logout URL"""
        return f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/logout?post_logout_redirect_uri={self.redirect_uri}"

def init_auth_session_state():
    """Initialize authentication-related session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'auth_state' not in st.session_state:
        st.session_state.auth_state = 'streamlit_auth'
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthManager()

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user info"""
    return st.session_state.get('user_info')

def require_auth(func):
    """Decorator to require authentication for functions"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            show_login_page()
            return None
        return func(*args, **kwargs)
    return wrapper