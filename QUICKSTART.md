# Quick Start Guide

Get up and running with the MACC Consumption Viewer in 5 minutes!

## 🚀 Fastest Start (SQLite - No Azure Required)

```bash
# 1. Clone and navigate
git clone https://github.com/tedescomicchidev/ConsumptionViewer.git
cd ConsumptionViewer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501` and use SQLite for storage (no Azure SQL required).

## 📊 Try It Out

1. **Upload Sample Data**
   - Click "Choose a CSV file"
   - Select `sample_data/sample_consumption_plan.csv`
   - Review validation results
   - Click "Proceed to Workspace"

2. **View Dashboards**
   - Navigate to the **Dashboard** tab
   - Select **CEO** role to see:
     - Total Year-1 ACR: CHF 2.5M
     - 10 workloads
     - Cumulative consumption curve
     - Top workloads by ACR

3. **Edit Data**
   - Go to **Data Editor** tab
   - Change "Ramp-Up Duration" for any workload
   - Click "Save Changes"
   - See computed fields update automatically

4. **Export Data**
   - Click "Export CSV" button
   - Download includes all computed fields

## 🎯 What You'll See

### CEO Dashboard
- **KPI Tiles**: Total ACR, workload count, average ramp duration
- **Cumulative Chart**: 12-month consumption trajectory
- **Scenario Split**: Breakdown by Rehost/Replatform/Refactor/New Build
- **Top Workloads**: Highest revenue workloads

### CFO Dashboard
- **Ramp vs Steady**: How much revenue comes from ramp-up vs steady-state
- **Pareto Chart**: Revenue concentration risk analysis
- **Risk Flags**: Automatically identified risks:
  - Long ramp-up duration
  - Low year-1 realization
  - Zero baseline with long ramp

### CTO Dashboard
- **Ramp Duration**: Distribution of ramp-up periods
- **Time to Steady-State**: Which workloads take longest
- **Service Footprint**: Most commonly used Azure services

## 🔧 Using Azure SQL (Optional)

If you want to use Azure SQL instead of SQLite:

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your Azure SQL details
DB_SERVER=your-server.database.windows.net
DB_NAME=ConsumptionViewerDB
DB_USERNAME=your-username
DB_PASSWORD=your-password

# 3. Run the app
streamlit run app.py
```

## 📝 CSV Format

Your CSV must include these columns:

| Column | Example |
|--------|---------|
| Workload | "Customer Portal" |
| Scenario | "Replatform" |
| Azure Services | "App Service, SQL Database" |
| Start Month | "Jan-2026" |
| Ramp-Up Duration (Months) | 6 |
| Ramp-Up Start Consumption (CHF) | 5000 |
| Steady-State Monthly Consumption (CHF) | 25000 |

Computed fields are calculated automatically:
- Avg Monthly Ramp-Up
- Total Ramp-Up
- Year-1 Steady-State Months
- Year-1 Steady-State Consumption
- Total Year-1 ACR

## 🧪 Running Tests

```bash
pytest
```

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed features
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for Azure deployment
- Review the [Product Requirements Document](docs/PRD.md) for specifications

## ❓ Common Issues

**Issue**: "No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

**Issue**: "Database connection failed"
- Check your Azure SQL credentials in `.env`
- Or remove `.env` to use SQLite

**Issue**: "CSV validation failed"
- Ensure all required columns are present
- Check sample CSV format: `sample_data/sample_consumption_plan.csv`

## 🤝 Need Help?

- Open an issue on GitHub
- Check existing issues for solutions
- Review documentation in the `docs/` folder
