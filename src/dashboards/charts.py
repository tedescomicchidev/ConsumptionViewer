"""Dashboard chart generation for CEO/CFO/CTO views"""

from typing import Any, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.utils.formulas import generate_monthly_curve
from src.utils.risk_analysis import calculate_all_risk_flags


def create_kpi_tiles(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create KPI tiles data.

    Returns dict with:
    - total_year1_acr: Total Year-1 ACR across all workloads
    - workload_count: Number of workloads
    - avg_ramp_duration: Average ramp-up duration
    """
    total_acr = df["Total Year-1 Estimated ACR (CHF)"].sum()
    workload_count = len(df)
    avg_ramp = df["Ramp-Up Duration (Months)"].mean()

    return {
        "total_year1_acr": total_acr,
        "workload_count": workload_count,
        "avg_ramp_duration": avg_ramp,
    }


def create_cumulative_consumption_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create cumulative 12-month consumption curve.
    Line chart showing cumulative consumption over 12 months.
    """
    # Generate monthly curves for all workloads
    monthly_totals = [0] * 12
    for _, row in df.iterrows():
        monthly_curve = generate_monthly_curve(row.to_dict())
        for i in range(12):
            monthly_totals[i] += monthly_curve[i]

    # Create cumulative values
    cumulative = []
    running_total = 0
    for monthly_value in monthly_totals:
        running_total += monthly_value
        cumulative.append(running_total)

    # Create chart
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(range(1, 13)),
            y=cumulative,
            mode="lines+markers",
            name="Cumulative Consumption",
            line=dict(color="#0078D4", width=3),
            marker=dict(size=8),
        )
    )

    fig.update_layout(
        title="Cumulative Year-1 Consumption",
        xaxis_title="Month",
        yaxis_title="Cumulative Consumption (CHF)",
        hovermode="x unified",
        template="plotly_white",
    )

    return fig


def create_scenario_split_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create ACR share by Scenario (donut/pie chart).
    """
    scenario_totals = df.groupby("Scenario")["Total Year-1 Estimated ACR (CHF)"].sum()

    fig = go.Figure(
        data=[
            go.Pie(
                labels=scenario_totals.index,
                values=scenario_totals.values,
                hole=0.4,
                marker=dict(colors=px.colors.qualitative.Set2),
            )
        ]
    )

    fig.update_layout(title="Year-1 ACR by Scenario", template="plotly_white", showlegend=True)

    return fig


def create_top_workloads_chart(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Create top N workloads by Total Year-1 ACR (horizontal bar chart).
    """
    # Sort by ACR and get top N
    top_workloads = df.nlargest(top_n, "Total Year-1 Estimated ACR (CHF)").sort_values(
        "Total Year-1 Estimated ACR (CHF)"
    )

    fig = go.Figure(
        go.Bar(
            x=top_workloads["Total Year-1 Estimated ACR (CHF)"],
            y=top_workloads["Workload"],
            orientation="h",
            marker=dict(color="#0078D4"),
        )
    )

    fig.update_layout(
        title=f"Top {top_n} Workloads by Year-1 ACR",
        xaxis_title="Year-1 ACR (CHF)",
        yaxis_title="Workload",
        template="plotly_white",
        height=400,
    )

    return fig


def create_ramp_vs_steady_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create stacked bar chart showing ramp-up vs steady-state consumption split.
    """
    # Calculate totals
    total_ramp = df["Total Ramp-Up Consumption (CHF)"].sum()
    total_steady = df["Year-1 Steady-State Consumption (CHF)"].sum()

    fig = go.Figure(
        data=[
            go.Bar(
                name="Ramp-Up",
                x=["Year-1 Consumption"],
                y=[total_ramp],
                marker=dict(color="#F25022"),
            ),
            go.Bar(
                name="Steady-State",
                x=["Year-1 Consumption"],
                y=[total_steady],
                marker=dict(color="#00A4EF"),
            ),
        ]
    )

    fig.update_layout(
        title="Ramp-Up vs Steady-State Consumption",
        barmode="stack",
        yaxis_title="Consumption (CHF)",
        template="plotly_white",
        showlegend=True,
    )

    return fig


def create_pareto_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create Pareto chart showing cumulative % of ACR by workload (concentration risk).
    """
    # Sort workloads by ACR descending
    sorted_df = df.sort_values("Total Year-1 Estimated ACR (CHF)", ascending=False).copy()

    # Calculate cumulative percentage
    total_acr = sorted_df["Total Year-1 Estimated ACR (CHF)"].sum()
    sorted_df["Cumulative %"] = (
        sorted_df["Total Year-1 Estimated ACR (CHF)"].cumsum() / total_acr * 100
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar chart for individual ACR
    fig.add_trace(
        go.Bar(
            name="ACR",
            x=sorted_df["Workload"],
            y=sorted_df["Total Year-1 Estimated ACR (CHF)"],
            marker=dict(color="#0078D4"),
        ),
        secondary_y=False,
    )

    # Line chart for cumulative %
    fig.add_trace(
        go.Scatter(
            name="Cumulative %",
            x=sorted_df["Workload"],
            y=sorted_df["Cumulative %"],
            mode="lines+markers",
            line=dict(color="#F25022", width=2),
            marker=dict(size=6),
        ),
        secondary_y=True,
    )

    fig.update_xaxes(title_text="Workload")
    fig.update_yaxes(title_text="ACR (CHF)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative %", secondary_y=True)

    fig.update_layout(
        title="ACR Concentration (Pareto Chart)",
        template="plotly_white",
        hovermode="x unified",
        height=400,
    )

    return fig


def create_risk_flags_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create risk flags table as DataFrame.
    """
    # Calculate risk flags for all rows
    data_dicts = df.to_dict("records")
    risk_flags = calculate_all_risk_flags(data_dicts)

    # Convert to DataFrame
    if not risk_flags:
        return pd.DataFrame(columns=["Workload", "Risk Type", "Severity", "Description"])

    risk_data = [
        {
            "Workload": flag.workload,
            "Risk Type": flag.risk_type,
            "Severity": flag.severity,
            "Description": flag.description,
        }
        for flag in risk_flags
    ]

    return pd.DataFrame(risk_data)


def create_ramp_duration_histogram(df: pd.DataFrame) -> go.Figure:
    """
    Create histogram of ramp-up duration distribution.
    """
    fig = px.histogram(
        df,
        x="Ramp-Up Duration (Months)",
        nbins=13,
        title="Ramp-Up Duration Distribution",
        labels={"Ramp-Up Duration (Months)": "Ramp-Up Duration", "count": "Number of Workloads"},
        color_discrete_sequence=["#0078D4"],
    )

    fig.update_layout(template="plotly_white", showlegend=False)

    return fig


def create_time_to_steady_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart showing time-to-steady-state by workload.
    """
    # Sort by ramp-up duration
    sorted_df = df.sort_values("Ramp-Up Duration (Months)", ascending=False).head(15)

    fig = go.Figure(
        go.Bar(
            x=sorted_df["Ramp-Up Duration (Months)"],
            y=sorted_df["Workload"],
            orientation="h",
            marker=dict(color="#00A4EF"),
        )
    )

    fig.update_layout(
        title="Time to Steady-State (Top 15 Longest)",
        xaxis_title="Ramp-Up Duration (Months)",
        yaxis_title="Workload",
        template="plotly_white",
        height=500,
    )

    return fig


def create_service_footprint_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart showing service footprint (keyword buckets).
    """
    # Parse Azure Services and count occurrences
    service_counts = {}
    for services_str in df["Azure Services"]:
        services = [s.strip() for s in str(services_str).split(",")]
        for service in services:
            if service:
                service_counts[service] = service_counts.get(service, 0) + 1

    # Sort by count and get top 15
    sorted_services = sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:15]

    if not sorted_services:
        return go.Figure()

    services, counts = zip(*sorted_services)

    fig = go.Figure(
        go.Bar(
            x=list(counts),
            y=list(services),
            orientation="h",
            marker=dict(color="#7FBA00"),
        )
    )

    fig.update_layout(
        title="Azure Service Usage (Top 15)",
        xaxis_title="Number of Workloads",
        yaxis_title="Service",
        template="plotly_white",
        height=500,
    )

    return fig
