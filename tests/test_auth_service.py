"""Tests for Microsoft Entra ID authentication service"""

import os
from unittest.mock import MagicMock, patch

from src.services.auth_service import (
    AuthConfig,
    EntraIDAuthService,
    get_current_user,
    is_authenticated,
)


def test_auth_config_not_configured():
    """Test AuthConfig when environment variables are not set"""
    with patch.dict(os.environ, {}, clear=True):
        config = AuthConfig()
        assert not config.is_configured()
        assert config.client_id == ""
        assert config.tenant_id == ""


def test_auth_config_configured():
    """Test AuthConfig when environment variables are set"""
    with patch.dict(
        os.environ,
        {
            "AZURE_CLIENT_ID": "test-client-id",
            "AZURE_TENANT_ID": "test-tenant-id",
            "AZURE_CLIENT_SECRET": "test-secret",
        },
    ):
        config = AuthConfig()
        assert config.is_configured()
        assert config.client_id == "test-client-id"
        assert config.tenant_id == "test-tenant-id"
        assert config.client_secret == "test-secret"
        assert "test-tenant-id" in config.authority


def test_auth_service_not_configured():
    """Test EntraIDAuthService when not configured"""
    with patch.dict(os.environ, {}, clear=True):
        service = EntraIDAuthService()
        assert not service.config.is_configured()
        assert service.get_msal_app() is None


def test_auth_service_get_msal_app():
    """Test EntraIDAuthService creates MSAL app when configured"""
    with patch.dict(
        os.environ,
        {
            "AZURE_CLIENT_ID": "test-client-id",
            "AZURE_TENANT_ID": "test-tenant-id",
            "AZURE_CLIENT_SECRET": "test-secret",
        },
    ):
        # Mock MSAL ConfidentialClientApplication
        with patch("src.services.auth_service.msal.ConfidentialClientApplication") as mock_msal:
            mock_app = MagicMock()
            mock_msal.return_value = mock_app

            service = EntraIDAuthService()
            app = service.get_msal_app()

            assert app is not None
            # Verify MSAL app was created with correct parameters
            mock_msal.assert_called_once()


def test_get_user_info():
    """Test extraction of user information from auth result"""
    service = EntraIDAuthService()

    auth_result = {
        "access_token": "test-token",
        "expires_in": 3600,
        "id_token_claims": {
            "preferred_username": "test@example.com",
            "name": "Test User",
            "oid": "user-id-123",
        },
    }

    user_info = service._get_user_info(auth_result)

    assert user_info["email"] == "test@example.com"
    assert user_info["name"] == "Test User"
    assert user_info["user_id"] == "user-id-123"
    assert user_info["access_token"] == "test-token"
    assert user_info["token_expires"] == 3600


def test_get_current_user_not_authenticated():
    """Test get_current_user when not authenticated"""
    import streamlit as st

    # Mock session state
    with patch.object(st, "session_state", {}):
        user = get_current_user()
        assert user == "demo_user"


def test_is_authenticated_false():
    """Test is_authenticated when user is not authenticated"""
    import streamlit as st

    with patch.object(st, "session_state", {}):
        assert not is_authenticated()


def test_is_authenticated_true():
    """Test is_authenticated when user is authenticated"""
    import streamlit as st

    with patch.object(st, "session_state", {"authenticated": True}):
        assert is_authenticated()


def test_get_current_user_authenticated():
    """Test get_current_user when authenticated"""
    import streamlit as st

    # Create a mock session state that behaves like a dict with attribute access
    class MockSessionState(dict):
        def __getattr__(self, key):
            return self.get(key)

    session_data = MockSessionState(
        {
            "authenticated": True,
            "user_info": {
                "email": "authenticated@example.com",
                "name": "Authenticated User",
            },
        }
    )

    with patch.object(st, "session_state", session_data):
        user = get_current_user()
        assert user == "authenticated@example.com"


def test_logout_clears_session():
    """Test logout clears authentication session data"""
    import streamlit as st

    session_data = {
        "authenticated": True,
        "user_info": {"email": "test@example.com"},
        "auth_flow": {"test": "data"},
        "current_user": "test@example.com",
    }

    with patch.object(st, "session_state", session_data):
        service = EntraIDAuthService()
        service.logout()

        # Check that authentication keys were removed
        assert "authenticated" not in st.session_state
        assert "user_info" not in st.session_state
        assert "auth_flow" not in st.session_state
        assert "current_user" not in st.session_state
