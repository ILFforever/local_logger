import streamlit as st
import json
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

st.set_page_config(
    page_title="LocalLogger Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_all_runs():
    """Load all runs from logs directory"""
    log_dir = Path("logs")
    if not log_dir.exists():
        return []

    runs = []
    for run_dir in log_dir.iterdir():
        if run_dir.is_dir():
            metrics_file = run_dir / "metrics.jsonl"
            config_file = run_dir / "config.json"
            summary_file = run_dir / "summary.json"

            if metrics_file.exists():
                run_data = {
                    "name": run_dir.name,
                    "path": run_dir,
                    "metrics": [],
                    "config": {},
                    "summary": {},
                }

                # Load config
                if config_file.exists():
                    with open(config_file) as f:
                        run_data["config"] = json.load(f)

                # Load summary
                if summary_file.exists():
                    with open(summary_file) as f:
                        run_data["summary"] = json.load(f)

                # Load metrics
                with open(metrics_file) as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            run_data["metrics"].append(entry)

                runs.append(run_data)

    return sorted(runs, key=lambda x: x["name"], reverse=True)


def get_metric_data(run, metric_name):
    """Extract metric data for plotting"""
    data = []
    for entry in run["metrics"]:
        if metric_name in entry:
            data.append(
                {
                    "step": entry.get("step", 0),
                    "value": entry[metric_name],
                    "timestamp": entry.get("timestamp", ""),
                }
            )
    return pd.DataFrame(data)


# Sidebar
st.sidebar.title("📊 LocalLogger")
st.sidebar.markdown("---")

runs = load_all_runs()

if not runs:
    st.warning("No runs found in `logs/` directory. Start training to see logs here.")
    st.stop()

# Run selection
run_names = [r["name"] for r in runs]
selected_run_name = st.sidebar.selectbox("Select Run", run_names)
selected_run = next(r for r in runs if r["name"] == selected_run_name)

# Auto-refresh
auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=True)
refresh_interval = st.sidebar.slider("Refresh interval (s)", 2, 30, 5) if auto_refresh else None

# Display run info
st.sidebar.markdown("---")
st.sidebar.subheader("Run Info")
st.sidebar.text(f"Name: {selected_run['name']}")
if selected_run["config"]:
    for key, val in selected_run["config"].items():
        if key != "start_time":
            st.sidebar.text(f"{key}: {val}")

if selected_run["summary"]:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Summary")
    if "metrics_summary" in selected_run["summary"]:
        for metric, stats in selected_run["summary"]["metrics_summary"].items():
            st.sidebar.metric(metric, f"{stats['final']:.6f}")

# Main content
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("📈 Live Metrics")

    # Get available metrics
    if selected_run["metrics"]:
        all_metrics = set()
        for entry in selected_run["metrics"]:
            all_metrics.update(
                k for k in entry.keys() if k not in ["step", "timestamp"]
            )

        selected_metric = st.selectbox("Select Metric", sorted(all_metrics))

        # Plot metric
        df = get_metric_data(selected_run, selected_metric)

        if not df.empty:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["step"],
                    y=df["value"],
                    mode="lines+markers",
                    name=selected_metric,
                    line=dict(color="#3498db", width=2),
                    marker=dict(size=4),
                )
            )
            fig.update_layout(
                title=f"{selected_metric} over Time",
                xaxis_title="Step",
                yaxis_title=selected_metric,
                hovermode="x unified",
                template="plotly_dark",
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No data for {selected_metric}")

with col2:
    st.subheader("📋 Recent Logs")

    if selected_run["metrics"]:
        df_metrics = pd.DataFrame(selected_run["metrics"])

        # Format for display
        display_cols = [col for col in df_metrics.columns if col not in ["timestamp"]]
        st.dataframe(
            df_metrics[display_cols].tail(20).sort_values("step", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

# Multiple metrics comparison
st.markdown("---")
st.subheader("🔍 Multi-Metric Comparison")

if selected_run["metrics"]:
    all_metrics = sorted(
        set(
            k
            for entry in selected_run["metrics"]
            for k in entry.keys()
            if k not in ["step", "timestamp"]
        )
    )
    selected_metrics = st.multiselect(
        "Select Metrics to Compare", all_metrics, default=all_metrics[:3]
    )

    if len(selected_metrics) >= 1:
        fig = go.Figure()
        colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]

        for i, metric in enumerate(selected_metrics):
            df = get_metric_data(selected_run, metric)
            if not df.empty:
                fig.add_trace(
                    go.Scatter(
                        x=df["step"],
                        y=df["value"],
                        mode="lines",
                        name=metric,
                        line=dict(color=colors[i % len(colors)], width=2),
                        yaxis=f"y{i + 1}" if i > 0 else None,
                    )
                )

        # Update layout
        fig.update_layout(
            title="Multiple Metrics",
            xaxis_title="Step",
            template="plotly_dark",
            height=500,
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

# Latest status
st.markdown("---")
st.subheader("🚀 Current Status")

if selected_run["metrics"]:
    latest = selected_run["metrics"][-1]
    cols = st.columns(4)

    for i, (key, val) in enumerate(latest.items()):
        if key not in ["step", "timestamp"] and i < 8:
            with cols[i % 4]:
                if isinstance(val, (int, float)):
                    st.metric(key.replace("_", " ").title(), f"{val:.6f}")
                else:
                    st.metric(key.replace("_", " ").title(), str(val))

# Schedule rerun AFTER page has fully rendered
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
