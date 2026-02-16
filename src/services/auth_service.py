"""Microsoft Entra ID (Azure AD) authentication service for Streamlit"""

import os
from typing import Dict, Optional, Tuple

import msal
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AuthConfig:
    """Authentication configuration from environment"""

    def __init__(self):
        self.client_id = os.getenv("AZURE_CLIENT_ID", "")
        self.tenant_id = os.getenv("AZURE_TENANT_ID", "")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET", "")
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["User.Read"]
        self.redirect_uri = os.getenv("REDIRECT_URI", "http://localhost:8501")

    def is_configured(self) -> bool:
        """Check if Entra ID is properly configured"""
        return bool(self.client_id and self.tenant_id and self.client_secret)


class EntraIDAuthService:
    """Service for Microsoft Entra ID authentication"""

    def __init__(self):
        self.config = AuthConfig()
        self._msal_app = None

    def get_msal_app(self) -> Optional[msal.ConfidentialClientApplication]:
        """Get or create MSAL application instance"""
        if not self.config.is_configured():
            return None

        if self._msal_app is None:
            self._msal_app = msal.ConfidentialClientApplication(
                self.config.client_id,
                authority=self.config.authority,
                client_credential=self.config.client_secret,
            )
        return self._msal_app

    def get_auth_url(self) -> Optional[str]:
        """
        Get authorization URL for user login.
        For Streamlit, we use device code flow instead of redirect flow.
        """
        app = self.get_msal_app()
        if not app:
            return None

        # For Streamlit apps, device code flow is more suitable
        flow = app.initiate_device_flow(scopes=self.config.scope)
        if "user_code" not in flow:
            return None

        # Store flow in session state for completion
        st.session_state.auth_flow = flow
        return flow["message"]

    def complete_device_flow(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Complete device code authentication flow.

        Returns:
            Tuple of (success, user_info, error_message)
        """
        app = self.get_msal_app()
        if not app or "auth_flow" not in st.session_state:
            return False, None, "Authentication not initialized"

        try:
            # Complete the device flow
            result = app.acquire_token_by_device_flow(st.session_state.auth_flow)

            if "access_token" in result:
                # Get user information
                user_info = self._get_user_info(result)
                return True, user_info, None
            else:
                error = result.get("error_description", "Authentication failed")
                return False, None, error

        except Exception as e:
            return False, None, str(e)

    def authenticate_with_username_password(
        self, username: str, password: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Authenticate user with username and password (Resource Owner Password Credentials flow).
        Note: This flow should only be used when redirect flow is not possible.

        Returns:
            Tuple of (success, user_info, error_message)
        """
        app = self.get_msal_app()
        if not app:
            return False, None, "Entra ID not configured"

        try:
            result = app.acquire_token_by_username_password(
                username, password, scopes=self.config.scope
            )

            if "access_token" in result:
                user_info = self._get_user_info(result)
                return True, user_info, None
            else:
                error = result.get("error_description", "Invalid credentials")
                return False, None, error

        except Exception as e:
            return False, None, str(e)

    def _get_user_info(self, auth_result: Dict) -> Dict:
        """Extract user information from authentication result"""
        id_token_claims = auth_result.get("id_token_claims", {})

        return {
            "email": id_token_claims.get("preferred_username", ""),
            "name": id_token_claims.get("name", ""),
            "user_id": id_token_claims.get("oid", ""),
            "access_token": auth_result.get("access_token", ""),
            "token_expires": auth_result.get("expires_in", 3600),
        }

    def get_cached_token(self) -> Optional[Dict]:
        """
        Get cached token if available.
        In Streamlit, tokens are stored in session state.
        """
        if "user_info" in st.session_state:
            return st.session_state.user_info
        return None

    def logout(self):
        """Clear authentication state"""
        # Clear session state authentication data
        auth_keys = [
            "authenticated",
            "user_info",
            "auth_flow",
            "current_user",
        ]
        for key in auth_keys:
            if key in st.session_state:
                del st.session_state[key]


# Singleton instance
_auth_service = None


def get_auth_service() -> EntraIDAuthService:
    """Get or create authentication service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = EntraIDAuthService()
    return _auth_service


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)


def get_current_user() -> str:
    """Get current authenticated user identifier"""
    if is_authenticated() and "user_info" in st.session_state:
        user_info = st.session_state.user_info
        return user_info.get("email", user_info.get("name", "authenticated_user"))
    return "demo_user"


def require_authentication() -> bool:
    """
    Check if authentication is required based on configuration.
    If Entra ID is not configured, authentication is optional (demo mode).

    Returns:
        True if authentication is required and user is authenticated, False otherwise
    """
    auth_service = get_auth_service()

    # If Entra ID is not configured, allow demo mode
    if not auth_service.config.is_configured():
        return True

    # If configured, require authentication
    return is_authenticated()
