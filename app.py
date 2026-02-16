"""Main Streamlit application for MACC Consumption Viewer"""
import io
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st

from src.database.connection import get_db_session, init_database
from src.dashboards.charts import (
    create_cumulative_consumption_chart,
    create_kpi_tiles,
    create_pareto_chart,
    create_ramp_duration_histogram,
    create_ramp_vs_steady_chart,
    create_risk_flags_table,
    create_scenario_split_chart,
    create_service_footprint_chart,
    create_time_to_steady_chart,
    create_top_workloads_chart,
)
from src.services.data_service import DataService
from src.services.validation import validate_csv_schema

# Page configuration
st.set_page_config(
    page_title="MACC Consumption Viewer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database
try:
    init_database()
except Exception as e:
    st.error(f"Database initialization failed: {e}")


def initialize_session_state():
    """Initialize session state variables"""
    if "current_dataset_id" not in st.session_state:
        st.session_state.current_dataset_id = None
    if "current_user" not in st.session_state:
        st.session_state.current_user = "demo_user"
    if "uploaded_data" not in st.session_state:
        st.session_state.uploaded_data = None
    if "dataset_name" not in st.session_state:
        st.session_state.dataset_name = None


def upload_screen():
    """Upload screen UI"""
    st.title("📤 MACC Consumption Plan Upload")

    st.markdown(
        """
    ### Welcome to the MACC Consumption Viewer
    
    Upload your consumption plan CSV file to get started. The file must match the v1 schema:
    - **Required columns:** Workload, Scenario, Azure Services, Start Month, Ramp-Up Duration (Months), 
      Ramp-Up Start Consumption (CHF), Steady-State Monthly Consumption (CHF)
    - **Computed columns** will be calculated automatically
    """
    )

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file", type=["csv"], help="Upload a CSV file matching the v1 schema"
    )

    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)

            st.subheader("📋 Preview")
            st.dataframe(df.head(10), use_container_width=True)

            # Validate
            st.subheader("✅ Validation")
            with st.spinner("Validating schema and data..."):
                validation_result = validate_csv_schema(df)

            if validation_result.is_valid():
                st.success(
                    f"✓ Validation passed! Found {len(df)} rows with all required columns."
                )

                # Show warnings if any
                if validation_result.warnings:
                    for warning in validation_result.warnings:
                        st.warning(warning)

                # Dataset name input
                dataset_name = st.text_input(
                    "Dataset Name (optional)",
                    value=uploaded_file.name,
                    help="Give this dataset a descriptive name",
                )

                # Proceed button
                if st.button("📊 Proceed to Workspace", type="primary"):
                    with st.spinner("Creating dataset..."):
                        try:
                            with get_db_session() as session:
                                data_service = DataService(
                                    session, current_user=st.session_state.current_user
                                )
                                dataset, error = data_service.create_dataset_from_csv(
                                    df, uploaded_file.name, dataset_name
                                )

                            if dataset:
                                st.session_state.current_dataset_id = str(dataset.dataset_id)
                                st.session_state.dataset_name = dataset.name
                                st.success("Dataset created successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to create dataset: {error}")

                        except Exception as e:
                            st.error(f"Error creating dataset: {e}")

            else:
                st.error(f"❌ Validation failed with {len(validation_result.errors)} errors")

                # Show error report
                error_df = validation_result.get_error_report()
                st.dataframe(error_df, use_container_width=True)

                # Offer download of error report
                csv_buffer = io.StringIO()
                error_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 Download Error Report",
                    data=csv_buffer.getvalue(),
                    file_name="validation_errors.csv",
                    mime="text/csv",
                )

        except Exception as e:
            st.error(f"Error reading file: {e}")


def workspace_screen():
    """Workspace screen with tabs"""
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("📊 Workspace")
        if st.session_state.dataset_name:
            st.caption(f"Dataset: {st.session_state.dataset_name}")

    with col2:
        if st.button("📤 Upload New Dataset"):
            st.session_state.current_dataset_id = None
            st.rerun()

    with col3:
        st.caption(f"User: {st.session_state.current_user}")

    # Load data
    try:
        with get_db_session() as session:
            data_service = DataService(session, current_user=st.session_state.current_user)
            df = data_service.get_dataset_data(uuid.UUID(st.session_state.current_dataset_id))

        if df is None or df.empty:
            st.error("No data found for this dataset")
            return

        # Tabs
        tab1, tab2 = st.tabs(["📈 Dashboard", "📝 Data Editor"])

        with tab1:
            dashboard_tab(df)

        with tab2:
            editor_tab(df)

    except Exception as e:
        st.error(f"Error loading workspace: {e}")


def dashboard_tab(df: pd.DataFrame):
    """Dashboard tab content"""
    # Role selector
    st.subheader("Executive Dashboard")
    role = st.selectbox(
        "Select Role View",
        ["CEO", "CFO", "CTO"],
        help="Choose the executive role to display relevant charts",
    )

    # KPI Tiles
    st.markdown("### 📊 Key Metrics")
    kpis = create_kpi_tiles(df)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Year-1 ACR",
            f"CHF {kpis['total_year1_acr']:,.0f}",
            help="Total estimated Annual Contract Revenue for Year 1",
        )
    with col2:
        st.metric(
            "Workload Count", f"{kpis['workload_count']}", help="Number of workloads in the plan"
        )
    with col3:
        st.metric(
            "Avg Ramp Duration",
            f"{kpis['avg_ramp_duration']:.1f} months",
            help="Average ramp-up duration across all workloads",
        )

    st.divider()

    # Role-specific charts
    if role == "CEO":
        st.markdown("### 📈 CEO Dashboard")

        # Cumulative consumption chart
        st.plotly_chart(
            create_cumulative_consumption_chart(df), use_container_width=True, key="ceo_cumulative"
        )

        col1, col2 = st.columns(2)
        with col1:
            # Scenario split
            st.plotly_chart(
                create_scenario_split_chart(df), use_container_width=True, key="ceo_scenario"
            )

        with col2:
            # Top workloads
            st.plotly_chart(
                create_top_workloads_chart(df, 10), use_container_width=True, key="ceo_top"
            )

    elif role == "CFO":
        st.markdown("### 💰 CFO Dashboard")

        col1, col2 = st.columns(2)
        with col1:
            # Ramp vs steady
            st.plotly_chart(
                create_ramp_vs_steady_chart(df), use_container_width=True, key="cfo_ramp"
            )

        with col2:
            # Pareto chart
            st.plotly_chart(create_pareto_chart(df), use_container_width=True, key="cfo_pareto")

        # Risk flags table
        st.markdown("### ⚠️ Risk Flags")
        risk_df = create_risk_flags_table(df)
        if not risk_df.empty:
            st.dataframe(risk_df, use_container_width=True, hide_index=True)
        else:
            st.info("No risk flags identified")

    elif role == "CTO":
        st.markdown("### 🔧 CTO Dashboard")

        col1, col2 = st.columns(2)
        with col1:
            # Ramp duration histogram
            st.plotly_chart(
                create_ramp_duration_histogram(df), use_container_width=True, key="cto_hist"
            )

        with col2:
            # Time to steady state
            st.plotly_chart(
                create_time_to_steady_chart(df), use_container_width=True, key="cto_time"
            )

        # Service footprint
        st.plotly_chart(
            create_service_footprint_chart(df), use_container_width=True, key="cto_services"
        )


def editor_tab(df: pd.DataFrame):
    """Data editor tab content"""
    st.subheader("Data Editor")

    st.info(
        "💡 **Tip:** You can edit cells directly. Computed columns (in gray) are read-only and will be recalculated when you save."
    )

    # Data editor
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        disabled=[
            "Avg Monthly Consumption During Ramp-Up (CHF)",
            "Total Ramp-Up Consumption (CHF)",
            "Year-1 Steady-State Months",
            "Year-1 Steady-State Consumption (CHF)",
            "Total Year-1 Estimated ACR (CHF)",
        ],
        key="data_editor",
    )

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("💾 Save Changes", type="primary"):
            with st.spinner("Saving changes..."):
                try:
                    with get_db_session() as session:
                        data_service = DataService(
                            session, current_user=st.session_state.current_user
                        )
                        revision, error = data_service.save_revision(
                            uuid.UUID(st.session_state.current_dataset_id),
                            edited_df,
                            change_summary="Manual edit from web UI",
                        )

                    if revision:
                        st.success("✓ Changes saved successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to save: {error}")

                except Exception as e:
                    st.error(f"Error saving changes: {e}")

    with col2:
        # Export button
        csv_buffer = io.StringIO()
        edited_df.to_csv(csv_buffer, index=False)

        st.download_button(
            label="📥 Export CSV",
            data=csv_buffer.getvalue(),
            file_name=f"consumption_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )


def main():
    """Main application entry point"""
    initialize_session_state()

    # Show upload or workspace based on state
    if st.session_state.current_dataset_id is None:
        upload_screen()
    else:
        workspace_screen()


if __name__ == "__main__":
    main()
