# MACC Consumption Plan Uploader, Editor & Executive Dashboard

A Python web application for managing Microsoft Azure Consumption Commitment (MACC) consumption plans with role-based executive dashboards.

## 🎯 Features

- **CSV Upload & Validation**: Upload consumption plans with automatic schema validation
- **Centralized Storage**: Azure SQL Database for persistent storage with revision history
- **Executive Dashboards**: Role-tailored views for CEO, CFO, and CTO
- **Data Editor**: Interactive spreadsheet-like editor with auto-computed fields
- **Risk Analysis**: Automated risk flag detection for consumption plans
- **Export/Import**: Full round-trip CSV export and re-import capabilities
- **Authentication**: Microsoft Entra ID integration for secure user authentication (optional)

## 📋 Requirements

- Python 3.11+
- Azure SQL Database (or SQLite for local development)
- Modern web browser

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/tedescomicchidev/ConsumptionViewer.git
cd ConsumptionViewer
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```
# For Azure SQL Database
DB_SERVER=your-server.database.windows.net
DB_NAME=ConsumptionViewerDB
DB_USERNAME=your-username
DB_PASSWORD=your-password

# For Microsoft Entra ID Authentication (Optional - v1.2)
# Leave blank to run in demo mode without authentication
AZURE_CLIENT_ID=your-application-client-id
AZURE_TENANT_ID=your-directory-tenant-id
AZURE_CLIENT_SECRET=your-client-secret

# For local SQLite (default if Azure SQL not configured)
# No configuration needed - will auto-create consumption_viewer.db
```

**Note**: If Entra ID credentials are not configured, the app runs in demo mode.

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 🔐 Authentication

The application supports two modes:

### Demo Mode (Default)
If Entra ID is not configured, you can use the app without authentication:
- Click "Continue in Demo Mode" on the login screen
- All operations are tracked as "demo@example.com"

### Microsoft Entra ID Authentication (v1.2)
For production use with real user authentication:
1. Register an application in Microsoft Entra ID (Azure Portal)
2. Configure environment variables in `.env`:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_CLIENT_SECRET`
3. Restart the application
4. Sign in with your Microsoft account

**See [AUTHENTICATION.md](AUTHENTICATION.md) for detailed setup instructions.**

## 📊 Usage

### Upload a Consumption Plan

1. Click "Choose a CSV file" on the upload screen
2. Select a CSV file matching the v1 schema (see below)
3. Review validation results
4. Click "Proceed to Workspace"

### View Dashboards

Navigate to the **Dashboard** tab and select a role:

- **CEO**: Year-1 ACR trends, scenario splits, top workloads
- **CFO**: Ramp vs steady-state analysis, Pareto charts, risk flags
- **CTO**: Ramp duration distribution, service footprint analysis

### Edit Data

1. Go to the **Data Editor** tab
2. Edit cells directly (input columns only)
3. Click "Save Changes" to create a new revision
4. Computed columns are automatically recalculated

### Export Data

Click "Export CSV" to download the current revision as a CSV file.

## 📝 CSV Schema (v1)

### Required Columns (Input)

| Column | Type | Description |
|--------|------|-------------|
| Workload | String | Workload name |
| Scenario | String | Rehost, Replatform, Refactor, or New Build |
| Azure Services | String | Comma-separated list of Azure services |
| Start Month | String | Start month (e.g., "Jan-2026") |
| Ramp-Up Duration (Months) | Integer | 0-12 months |
| Ramp-Up Start Consumption (CHF) | Decimal | Starting consumption (CHF) |
| Steady-State Monthly Consumption (CHF) | Decimal | Target monthly consumption (CHF) |

### Computed Columns (Auto-calculated)

| Column | Formula |
|--------|---------|
| Avg Monthly Consumption During Ramp-Up (CHF) | (Start + Steady) / 2 |
| Total Ramp-Up Consumption (CHF) | Avg × Duration |
| Year-1 Steady-State Months | 12 - Duration |
| Year-1 Steady-State Consumption (CHF) | Months × Steady |
| Total Year-1 Estimated ACR (CHF) | Ramp + Steady |

## 🏗️ Architecture

```
ConsumptionViewer/
├── app.py                      # Main Streamlit application
├── src/
│   ├── models/
│   │   ├── database.py         # SQLAlchemy models
│   │   └── schema.py           # CSV schema definitions
│   ├── database/
│   │   └── connection.py       # Database connection management
│   ├── services/
│   │   ├── data_service.py     # Business logic for datasets
│   │   └── validation.py       # CSV validation service
│   ├── utils/
│   │   ├── formulas.py         # Computation engine
│   │   └── risk_analysis.py    # Risk flag calculator
│   └── dashboards/
│       └── charts.py           # Chart generation
├── sql/
│   └── schema.sql              # Database schema DDL
├── sample_data/
│   └── sample_consumption_plan.csv
└── tests/                      # Unit and integration tests
```

## 🧪 Testing

Run tests with pytest:

```bash
pytest
```

With coverage:

```bash
pytest --cov=src --cov-report=html
```

## 🚢 Deployment

### Azure App Service (Linux)

1. **Create App Service**:
```bash
az webapp create \
  --resource-group <your-rg> \
  --plan <your-plan> \
  --name <your-app-name> \
  --runtime "PYTHON:3.11"
```

2. **Configure Application Settings**:
```bash
az webapp config appsettings set \
  --resource-group <your-rg> \
  --name <your-app-name> \
  --settings \
    DB_SERVER=<your-server> \
    DB_NAME=<your-db> \
    DB_USERNAME=<your-user> \
    DB_PASSWORD=<your-password>
```

3. **Deploy**:
```bash
az webapp up --name <your-app-name> --resource-group <your-rg>
```

### Docker (Alternative)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 🔐 Security

- Uses parameterized queries to prevent SQL injection
- Environment variables for sensitive credentials
- Supports Azure Managed Identity for database access
- Audit logging for all data modifications

## 📚 Documentation

- [Product Requirements Document (PRD)](docs/PRD.md) - Full specification
- [API Documentation](docs/API.md) - Service layer APIs
- [Database Schema](sql/schema.sql) - Database design
- [Authentication Guide](AUTHENTICATION.md) - Microsoft Entra ID setup
- [Deployment Guide](DEPLOYMENT.md) - Azure deployment instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Copyright © 2026 Michele Tedesco. All rights reserved.

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Contact: Michele Tedesco

## 🎯 Roadmap

- [x] MVP: Upload, edit, export, dashboards
- [ ] v1.1: Multiple dataset management, revision diff
- [ ] v1.2: Microsoft Entra ID integration
- [ ] v2.0: FastAPI + React frontend, real-time collaboration