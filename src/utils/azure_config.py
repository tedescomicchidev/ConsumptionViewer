"""Azure deployment configuration and utilities"""

import os
from typing import Optional


def get_app_insights_connection_string() -> Optional[str]:
    """Get Application Insights connection string from environment"""
    return os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")


def is_azure_environment() -> bool:
    """Check if running in Azure App Service"""
    return os.getenv("WEBSITE_SITE_NAME") is not None


def get_azure_webapp_name() -> Optional[str]:
    """Get Azure Web App name"""
    return os.getenv("WEBSITE_SITE_NAME")
