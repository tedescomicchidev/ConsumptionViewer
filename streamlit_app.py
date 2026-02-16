from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.compute import build_monthly_series, risk_flags
from app.db import create_dataset_with_revision, get_dataset_rows, init_db, save_revision
from app.schema import REQUIRED_COLUMNS
from app.validation import validate_and_compute

st.set_page_config(page_title="Consumption Viewer", layout="wide")
init_db()

st.title("MACC Consumption Plan Uploader & Executive Dashboard")
actor = st.sidebar.text_input("User", value="local.user@contoso.com")

if "dataset_id" not in st.session_state:
    st.session_state.dataset_id = None

upload_col, action_col = st.columns([3, 1])
with upload_col:
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
with action_col:
    dataset_name = st.text_input("Dataset name", value="")

if uploaded_file is not None and st.button("Validate & Upload", type="primary"):
    input_df = pd.read_csv(uploaded_file)
    computed_df, issues = validate_and_compute(input_df)
    if issues:
        st.error("Validation failed. Fix errors and retry.")
        issue_df = pd.DataFrame([issue.__dict__ for issue in issues])
        st.dataframe(issue_df, use_container_width=True)
        csv = issue_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download error report CSV", data=csv, file_name="validation_errors.csv")
    else:
        ds_id = create_dataset_with_revision(
            computed_df,
            filename=uploaded_file.name,
            actor=actor,
            dataset_name=dataset_name or uploaded_file.name,
        )
        st.session_state.dataset_id = ds_id
        st.success("Dataset uploaded successfully.")

if st.session_state.dataset_id:
    df, meta = get_dataset_rows(st.session_state.dataset_id)
    st.subheader(f"Workspace — {meta['name']}")
    tab1, tab2 = st.tabs(["Executive Dashboard", "Table Editor"])

    with tab1:
        role = st.selectbox("Role preset", ["CEO", "CFO", "CTO"])
        scenarios = sorted(df["Scenario"].dropna().unique().tolist())
        selected_scenarios = st.multiselect("Scenario filter", scenarios, default=scenarios)
        filtered = df[df["Scenario"].isin(selected_scenarios)]

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Year-1 ACR", f"CHF {filtered['Total Year-1 Estimated ACR (CHF)'].sum():,.2f}")
        k2.metric("# Workloads", f"{filtered['Workload'].nunique()}")
        k3.metric("Avg Ramp Duration", f"{filtered['Ramp-Up Duration (Months)'].mean():.2f}")

        monthly = build_monthly_series(filtered)
        aggregate = monthly.groupby("Month", as_index=False)["Consumption"].sum()
        aggregate["Cumulative"] = aggregate["Consumption"].cumsum()

        if role == "CEO":
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.line(aggregate, x="Month", y="Cumulative", title="Cumulative 12-month Consumption"), use_container_width=True)
            with c2:
                by_scenario = filtered.groupby("Scenario", as_index=False)["Total Year-1 Estimated ACR (CHF)"].sum()
                st.plotly_chart(px.pie(by_scenario, names="Scenario", values="Total Year-1 Estimated ACR (CHF)", title="ACR Share by Scenario"), use_container_width=True)

            top10 = filtered.nlargest(10, "Total Year-1 Estimated ACR (CHF)")
            st.plotly_chart(px.bar(top10, x="Workload", y="Total Year-1 Estimated ACR (CHF)", title="Top 10 Workloads by Year-1 ACR"), use_container_width=True)

        if role == "CFO":
            split = pd.DataFrame(
                {
                    "Category": ["Ramp-Up", "Steady-State"],
                    "Value": [filtered["Total Ramp-Up Consumption (CHF)"].sum(), filtered["Year-1 Steady-State Consumption (CHF)"].sum()],
                }
            )
            st.plotly_chart(px.bar(split, x="Category", y="Value", title="Ramp-Up vs Steady-State Share"), use_container_width=True)

            pareto = filtered.groupby("Workload", as_index=False)["Total Year-1 Estimated ACR (CHF)"].sum().sort_values("Total Year-1 Estimated ACR (CHF)", ascending=False)
            pareto["Cumulative %"] = pareto["Total Year-1 Estimated ACR (CHF)"].cumsum() / pareto["Total Year-1 Estimated ACR (CHF)"].sum() * 100
            st.plotly_chart(px.line(pareto, x="Workload", y="Cumulative %", title="Pareto Concentration"), use_container_width=True)

            st.dataframe(risk_flags(filtered), use_container_width=True)

        if role == "CTO":
            st.plotly_chart(px.histogram(filtered, x="Ramp-Up Duration (Months)", title="Ramp-Up Duration Distribution"), use_container_width=True)
            st.plotly_chart(px.bar(filtered, x="Workload", y="Ramp-Up Duration (Months)", title="Time to Steady-State by Workload"), use_container_width=True)

            services = (
                filtered.assign(Service=filtered["Azure Services"].str.split(","))
                .explode("Service")
                .assign(Service=lambda d: d["Service"].str.strip())
                .groupby("Service", as_index=False)
                .size()
                .rename(columns={"size": "Count"})
                .sort_values("Count", ascending=False)
                .head(15)
            )
            st.plotly_chart(px.bar(services, x="Service", y="Count", title="Service Footprint"), use_container_width=True)

    with tab2:
        st.caption("Editable columns: required input columns. Computed columns are overwritten on save.")
        editable_df = st.data_editor(df[REQUIRED_COLUMNS], num_rows="dynamic", use_container_width=True, key="editor")
        summary = st.text_input("Change summary", value="Manual edit")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Save Revision"):
                computed_df, issues = validate_and_compute(pd.DataFrame(editable_df))
                if issues:
                    st.error("Cannot save due to validation errors.")
                    st.dataframe(pd.DataFrame([i.__dict__ for i in issues]), use_container_width=True)
                else:
                    save_revision(st.session_state.dataset_id, computed_df, actor=actor, change_summary=summary)
                    st.success("Revision saved.")
                    st.rerun()

        with c2:
            csv_data = df.to_csv(index=False)
            st.download_button(
                "Export Latest Revision CSV",
                data=csv_data,
                file_name=f"{meta['name']}_latest.csv",
                mime="text/csv",
            )
else:
    st.info("Upload a valid CSV to begin.")
