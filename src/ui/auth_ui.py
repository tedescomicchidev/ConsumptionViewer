"""Authentication UI components for Streamlit"""

import streamlit as st

from src.services.auth_service import get_auth_service, get_current_user, is_authenticated


def show_login_screen():
    """Display login screen for Entra ID authentication"""
    st.title("🔐 MACC Consumption Viewer - Login")

    auth_service = get_auth_service()

    st.markdown(
        """
    ### Welcome to MACC Consumption Viewer

    Please sign in with your Microsoft account to continue.
    """
    )

    # Check if we're in demo mode (no Entra ID configured)
    if not auth_service.config.is_configured():
        st.info(
            """
        **Demo Mode**: Entra ID is not configured. 

        You can proceed without authentication for testing purposes.
        To enable authentication, configure the following environment variables:
        - AZURE_CLIENT_ID
        - AZURE_TENANT_ID  
        - AZURE_CLIENT_SECRET
        """
        )

        if st.button("Continue in Demo Mode", type="primary"):
            st.session_state.authenticated = True
            st.session_state.user_info = {
                "email": "demo@example.com",
                "name": "Demo User",
                "user_id": "demo-user-id",
            }
            st.session_state.current_user = "demo@example.com"
            st.rerun()
        return

    # Entra ID is configured - show authentication options
    st.markdown("---")

    tab1, tab2 = st.tabs(["Username/Password", "Device Code"])

    with tab1:
        st.markdown("#### Sign in with Username and Password")
        st.info(
            """
        **Note**: Username/Password flow requires specific Entra ID app configuration.
        If this doesn't work, try the Device Code flow instead.
        """
        )

        with st.form("login_form"):
            username = st.text_input(
                "Email / Username", placeholder="user@example.com", key="login_username"
            )
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Sign In", type="primary")

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    with st.spinner("Authenticating..."):
                        success, user_info, error = (
                            auth_service.authenticate_with_username_password(username, password)
                        )

                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.session_state.current_user = user_info.get(
                            "email", user_info.get("name", "authenticated_user")
                        )
                        st.success("✓ Authentication successful!")
                        st.rerun()
                    else:
                        st.error(f"Authentication failed: {error}")

    with tab2:
        st.markdown("#### Sign in with Device Code")
        st.info(
            """
        This flow works best for Streamlit apps:
        1. Click 'Get Device Code' below
        2. Copy the code shown
        3. Visit the link and enter your code
        4. After authentication, click 'Complete Sign In'
        """
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔑 Get Device Code", key="get_device_code"):
                message = auth_service.get_auth_url()
                if message:
                    st.session_state.device_code_message = message
                else:
                    st.error("Failed to initiate device code flow")

        # Display device code if available
        if "device_code_message" in st.session_state:
            st.code(st.session_state.device_code_message, language=None)

            with col2:
                if st.button("✓ Complete Sign In", type="primary", key="complete_device"):
                    with st.spinner("Checking authentication status..."):
                        success, user_info, error = auth_service.complete_device_flow()

                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.session_state.current_user = user_info.get(
                            "email", user_info.get("name", "authenticated_user")
                        )
                        # Clear device code message
                        if "device_code_message" in st.session_state:
                            del st.session_state.device_code_message
                        st.success("✓ Authentication successful!")
                        st.rerun()
                    else:
                        st.error(f"Authentication failed: {error}")
                        st.info("Please ensure you completed the device code flow.")


def show_user_info():
    """Display current user information in sidebar or header"""
    if is_authenticated():
        user_name = get_current_user()
        st.sidebar.markdown(f"**User:** {user_name}")

        # Logout button
        if st.sidebar.button("🚪 Logout"):
            auth_service = get_auth_service()
            auth_service.logout()
            st.rerun()
    else:
        st.sidebar.info("Not authenticated")


def show_user_header():
    """Display user information in main content area header"""
    if is_authenticated():
        user_info = st.session_state.get("user_info", {})
        user_name = user_info.get("name", get_current_user())
        user_email = user_info.get("email", "")

        return f"{user_name}" if user_name else user_email
    return "Demo User"
