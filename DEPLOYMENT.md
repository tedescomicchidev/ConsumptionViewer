# Azure Deployment Guide

This guide provides step-by-step instructions for deploying the MACC Consumption Viewer to Azure App Service.

## Prerequisites

- Azure subscription
- Azure CLI installed (`az` command)
- Azure SQL Database provisioned
- Docker (optional, for container deployment)

## Option 1: Deploy via Azure CLI

### 1. Create Azure Resources

```bash
# Set variables
RESOURCE_GROUP="consumption-viewer-rg"
LOCATION="westeurope"
APP_SERVICE_PLAN="consumption-viewer-plan"
WEB_APP_NAME="consumption-viewer-app"
SQL_SERVER="consumption-viewer-sql"
SQL_DATABASE="ConsumptionViewerDB"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service Plan (Linux)
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "PYTHON:3.11"

# Create Azure SQL Server
az sql server create \
  --name $SQL_SERVER \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user sqladmin \
  --admin-password 'YourSecurePassword123!'

# Create Azure SQL Database
az sql db create \
  --name $SQL_DATABASE \
  --server $SQL_SERVER \
  --resource-group $RESOURCE_GROUP \
  --service-objective S0

# Configure firewall to allow Azure services
az sql server firewall-rule create \
  --name AllowAzureServices \
  --server $SQL_SERVER \
  --resource-group $RESOURCE_GROUP \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### 2. Configure Application Settings

```bash
# Get SQL connection details
SQL_FQDN=$(az sql server show --name $SQL_SERVER --resource-group $RESOURCE_GROUP --query fullyQualifiedDomainName -o tsv)

# Set application settings
az webapp config appsettings set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    DB_SERVER=$SQL_FQDN \
    DB_NAME=$SQL_DATABASE \
    DB_USERNAME=sqladmin \
    DB_PASSWORD='YourSecurePassword123!' \
    DB_DRIVER="ODBC Driver 18 for SQL Server" \
    APP_ENV=production \
    LOG_LEVEL=INFO \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

### 3. Deploy Application

```bash
# Deploy from local directory
az webapp up \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --runtime "PYTHON:3.11"

# OR deploy from GitHub
az webapp deployment source config \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --repo-url https://github.com/tedescomicchidev/ConsumptionViewer \
  --branch main \
  --manual-integration
```

### 4. Configure Startup Command

```bash
# Set custom startup command for Streamlit
az webapp config set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "streamlit run app.py --server.port=8000 --server.address=0.0.0.0 --server.headless=true"
```

## Option 2: Deploy via Docker Container

### 1. Build and Push Docker Image

```bash
# Login to Azure Container Registry (or Docker Hub)
az acr login --name myregistry

# Build image
docker build -t consumption-viewer:latest .

# Tag for registry
docker tag consumption-viewer:latest myregistry.azurecr.io/consumption-viewer:latest

# Push to registry
docker push myregistry.azurecr.io/consumption-viewer:latest
```

### 2. Deploy Container to App Service

```bash
# Create Web App from container
az webapp create \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --deployment-container-image-name myregistry.azurecr.io/consumption-viewer:latest

# Configure container settings
az webapp config container set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name myregistry.azurecr.io/consumption-viewer:latest \
  --docker-registry-server-url https://myregistry.azurecr.io
```

## Option 3: Deploy via GitHub Actions

### 1. Get Publish Profile

```bash
# Download publish profile
az webapp deployment list-publishing-profiles \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --xml > publish-profile.xml
```

### 2. Add Secret to GitHub

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Name: `AZURE_WEBAPP_PUBLISH_PROFILE`
5. Value: Paste contents of `publish-profile.xml`

### 3. Trigger Deployment

Push to the `main` branch or manually trigger the workflow:

```bash
git push origin main
```

## Post-Deployment

### 1. Initialize Database

Access the application URL and it will automatically create database tables on first run, or run schema manually:

```bash
# Install Azure CLI extension for SQL
az extension add --name db

# Run schema script
az sql db query \
  --server $SQL_SERVER \
  --database $SQL_DATABASE \
  --name $RESOURCE_GROUP \
  --query "$(cat sql/schema.sql)"
```

### 2. Configure Managed Identity (Recommended)

```bash
# Enable system-assigned managed identity
az webapp identity assign \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP

# Get the identity principal ID
PRINCIPAL_ID=$(az webapp identity show \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Grant SQL permissions
az sql server ad-admin create \
  --server $SQL_SERVER \
  --resource-group $RESOURCE_GROUP \
  --display-name $WEB_APP_NAME \
  --object-id $PRINCIPAL_ID
```

### 3. Enable Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app consumption-viewer-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --application-type web

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app consumption-viewer-insights \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey -o tsv)

# Configure Web App
az webapp config appsettings set \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=$INSTRUMENTATION_KEY"
```

## Monitoring and Logs

### View Live Logs

```bash
az webapp log tail \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### Enable Logging

```bash
az webapp log config \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --application-logging filesystem \
  --level information
```

## Scaling

### Manual Scale

```bash
# Scale up (change App Service Plan)
az appservice plan update \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku P1V2

# Scale out (add instances)
az appservice plan update \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --number-of-workers 3
```

### Auto-scale

```bash
# Enable auto-scale
az monitor autoscale create \
  --name consumption-viewer-autoscale \
  --resource-group $RESOURCE_GROUP \
  --resource $APP_SERVICE_PLAN \
  --resource-type Microsoft.Web/serverFarms \
  --min-count 1 \
  --max-count 5 \
  --count 2
```

## Troubleshooting

### Check Application Status

```bash
az webapp show \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query state
```

### Restart Application

```bash
az webapp restart \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

### SSH into Container

```bash
az webapp ssh \
  --name $WEB_APP_NAME \
  --resource-group $RESOURCE_GROUP
```

## Security Best Practices

1. **Use Managed Identity** instead of connection strings
2. **Store secrets in Key Vault**
3. **Enable HTTPS only**
4. **Configure CORS** if accessing from other domains
5. **Enable authentication** via Microsoft Entra ID
6. **Regular security updates** for dependencies

## Cost Optimization

- Use **B1** tier for development/testing
- Use **P1V2** or higher for production
- Enable **auto-scale** based on demand
- Use **Azure SQL serverless** for variable workloads
- Monitor costs with **Azure Cost Management**

## Support

For issues with deployment:
- Check application logs: `az webapp log tail`
- Review Application Insights for errors
- Verify database connectivity
- Check firewall rules on SQL Server
