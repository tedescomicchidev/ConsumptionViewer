# Microsoft Entra ID Authentication Guide

This guide explains how to set up and configure Microsoft Entra ID (formerly Azure Active Directory) authentication for the MACC Consumption Viewer application.

## Overview

The application supports two authentication modes:

1. **Demo Mode** (default): No authentication required, uses a demo user
2. **Entra ID Mode**: Full Microsoft authentication with real user accounts

## Prerequisites

- Azure subscription with access to Microsoft Entra ID
- Permissions to register applications in Entra ID
- Basic understanding of OAuth 2.0 and OpenID Connect

## Step 1: Register Application in Microsoft Entra ID

### 1.1 Access Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Microsoft Entra ID** (formerly Azure Active Directory)
3. Select **App registrations** from the left menu
4. Click **+ New registration**

### 1.2 Configure App Registration

**Basic Information:**
- **Name**: `MACC Consumption Viewer` (or your preferred name)
- **Supported account types**: 
  - Select "Accounts in this organizational directory only" for single tenant
  - Or "Accounts in any organizational directory" for multi-tenant
- **Redirect URI**: Leave blank for now (we'll use device code flow)

Click **Register**.

### 1.3 Note Key Information

After registration, note these values (you'll need them for configuration):

1. **Application (client) ID**: Copy this value
2. **Directory (tenant) ID**: Copy this value

### 1.4 Create Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **+ New client secret**
3. Add a description (e.g., "ConsumptionViewer Secret")
4. Select expiration (e.g., 24 months)
5. Click **Add**
6. **IMPORTANT**: Copy the secret **Value** immediately (it won't be shown again)

### 1.5 Configure API Permissions

1. Go to **API permissions**
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Select **Delegated permissions**
5. Add these permissions:
   - `User.Read` (should be added by default)
6. Click **Add permissions**
7. Click **Grant admin consent** (if you have admin rights)

### 1.6 (Optional) Enable Username/Password Flow

If you want to support username/password authentication:

1. Go to **Authentication**
2. Under **Advanced settings**, set **Allow public client flows** to **Yes**
3. Click **Save**

**Note**: Device code flow is recommended as it's more secure and doesn't require this setting.

## Step 2: Configure Application

### 2.1 Set Environment Variables

Create or update your `.env` file with the following values:

```env
# Microsoft Entra ID Configuration
AZURE_CLIENT_ID=<your-application-client-id>
AZURE_TENANT_ID=<your-directory-tenant-id>
AZURE_CLIENT_SECRET=<your-client-secret-value>

# Optional: Custom redirect URI (defaults to http://localhost:8501)
REDIRECT_URI=http://localhost:8501

# Database Configuration (required)
DB_SERVER=your-azure-sql-server.database.windows.net
DB_NAME=ConsumptionViewerDB
DB_USERNAME=your-db-username
DB_PASSWORD=your-db-password

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
```

### 2.2 Environment Variable Details

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_CLIENT_ID` | Yes* | Application (client) ID from Entra ID |
| `AZURE_TENANT_ID` | Yes* | Directory (tenant) ID from Entra ID |
| `AZURE_CLIENT_SECRET` | Yes* | Client secret value from Entra ID |
| `REDIRECT_URI` | No | Redirect URI for OAuth flow (default: http://localhost:8501) |

\* Required only if you want to enable Entra ID authentication. Without these, the app runs in demo mode.

## Step 3: Run the Application

### 3.1 Start the Application

```bash
streamlit run app.py
```

### 3.2 Authentication Experience

**If Entra ID is configured:**

The application will show a login screen with two authentication options:

#### Option 1: Username/Password
1. Enter your Microsoft account email
2. Enter your password
3. Click "Sign In"

**Note**: This requires the "Allow public client flows" setting enabled (Step 1.6).

#### Option 2: Device Code Flow (Recommended)
1. Click "Get Device Code"
2. Copy the code displayed
3. Visit the link shown (e.g., https://microsoft.com/devicelogin)
4. Enter the code
5. Sign in with your Microsoft account
6. Return to the app and click "Complete Sign In"

**If Entra ID is not configured:**

The application will show a "Demo Mode" message with a button to continue without authentication.

## Step 4: Verify Authentication

### 4.1 Check User Information

After successful login:
- Your name/email will appear in the sidebar under "User"
- The workspace header will show your authenticated user
- All audit logs will track your user email/name

### 4.2 Logout

Click the "🚪 Logout" button in the sidebar to:
- Clear authentication tokens
- Clear user information from session
- Return to the login screen

## Troubleshooting

### Error: "Authentication failed: invalid_grant"

**Cause**: Invalid credentials or user account not allowed

**Solutions**:
- Verify username and password are correct
- Ensure user account is in the correct tenant
- Check if account requires MFA (use device code flow instead)

### Error: "Entra ID not configured"

**Cause**: Environment variables not set correctly

**Solutions**:
- Verify `.env` file exists in the project root
- Check that all three variables are set: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`
- Restart the application after updating `.env`

### Device Code Flow Not Working

**Solutions**:
- Ensure you're visiting the correct URL (microsoft.com/devicelogin)
- Complete the authentication within the time limit (usually 15 minutes)
- Try clicking "Complete Sign In" again after authenticating
- Check browser console for errors

### Username/Password Flow Not Working

**Solutions**:
- Verify "Allow public client flows" is enabled (Step 1.6)
- Try device code flow instead (more reliable)
- Check if your account requires MFA (if so, use device code flow)

## Security Best Practices

### Production Deployment

1. **Use HTTPS**: Always deploy with HTTPS in production
   ```bash
   # Configure in Azure App Service or use reverse proxy
   ```

2. **Secure Client Secret**: Use Azure Key Vault instead of environment variables
   ```python
   # Example with Key Vault
   from azure.keyvault.secrets import SecretClient
   
   secret = key_vault_client.get_secret("AZURE_CLIENT_SECRET")
   ```

3. **Token Management**:
   - Tokens are stored in Streamlit session state (server-side)
   - Tokens are automatically cleared on logout
   - Session expires when browser is closed

4. **Network Security**:
   - Use Azure Virtual Network for database connectivity
   - Enable firewall rules to restrict access
   - Consider using Private Endpoints

### Monitoring

Enable audit logging to track authentication events:

```sql
-- Query audit log for authentication events
SELECT 
    actor,
    action,
    timestamp,
    details_json
FROM audit_log
WHERE action IN ('LOGIN', 'LOGOUT')
ORDER BY timestamp DESC;
```

## Advanced Configuration

### Multi-Tenant Support

To support users from multiple organizations:

1. In app registration, select "Accounts in any organizational directory"
2. Update authority in code:
   ```python
   authority = "https://login.microsoftonline.com/common"
   ```

### Custom Scopes

To request additional permissions:

1. Add permissions in Azure Portal (Step 1.5)
2. Update scope in `.env`:
   ```env
   AZURE_SCOPES=User.Read,email,profile
   ```

### Token Caching

For production, consider implementing persistent token caching:

```python
# Example with Redis
import redis
token_cache = redis.Redis(host='localhost', port=6379, db=0)
```

## Testing Authentication

### Local Testing

1. Set up test credentials in `.env`
2. Run application: `streamlit run app.py`
3. Test both authentication flows
4. Verify user information appears correctly
5. Test logout functionality

### Integration Testing

```bash
# Run authentication tests
pytest tests/test_auth_service.py -v
```

## Support

### Common Questions

**Q: Can I use personal Microsoft accounts?**
A: No, only organizational accounts (work/school) are supported by default. To support personal accounts, configure "Accounts in any Microsoft identity" during app registration.

**Q: How long do sessions last?**
A: Sessions last until the browser is closed or the user logs out. Tokens typically expire after 1 hour but are automatically refreshed.

**Q: Is MFA supported?**
A: Yes, device code flow supports MFA. Username/password flow may not work with MFA-enabled accounts.

**Q: Can I use this with Azure B2C?**
A: This implementation is designed for Entra ID (Azure AD). For B2C, you'll need to modify the authority URL and flow.

## References

- [Microsoft Identity Platform Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [Azure AD App Registration Guide](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Device Code Flow](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-device-code)

## Appendix: Flow Diagrams

### Device Code Flow

```
User → App: Click "Get Device Code"
App → Entra ID: Initiate device flow
Entra ID → App: Return code & URL
App → User: Display code & URL
User → Browser: Visit URL, enter code
Browser → Entra ID: Authenticate
User → App: Click "Complete Sign In"
App → Entra ID: Check authentication
Entra ID → App: Return tokens
App → User: Authenticated session
```

### Username/Password Flow

```
User → App: Enter credentials
App → Entra ID: Submit credentials
Entra ID → App: Return tokens
App → User: Authenticated session
```
