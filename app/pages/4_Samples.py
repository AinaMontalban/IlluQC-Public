"""Samples page – per-sample QC metrics

Visualise sample-level quality metrics for a selected sample.
When the sample appears in multiple runs, each run is shown in its own tab.
"""

import streamlit as st
import pandas as pd
import altair as alt

from db import get_engine
import queries
from constants import COLUMN_LABELS

st.set_page_config(page_title="Sample QC", layout="wide")

st.write("# Sample QC Metrics")

engine = get_engine()


# ---------------------------------------------------------------------------
# Data loading – all sample IDs that have QC data
# ---------------------------------------------------------------------------

sample_ids_df = queries.get_sample_qc_sample_ids(engine)

if sample_ids_df.empty:
    st.warning("No sample QC data found in the database.")
    st.stop()

sample_ids_sorted = sample_ids_df["sample_id"].tolist()

# ---------------------------------------------------------------------------
# Sample selector
# ---------------------------------------------------------------------------

sample_option = st.selectbox(
    "Select Sample:",
    sample_ids_sorted,
    index=None,
    placeholder="Write sample ID...",
)

if sample_option is None:
    st.info("Please select a Sample ID to see QC details.")
    st.stop()

if sample_option not in sample_ids_sorted:
    st.warning("Sample ID not found. Please select a valid Sample ID.")
    st.stop()

# ---------------------------------------------------------------------------
# Fetch all QC metrics for the selected sample (across all runs)
# ---------------------------------------------------------------------------

metrics_df = queries.get_sample_qc_metrics_for_sample(engine, sample_option)

if metrics_df.empty:
    st.info("No QC metrics found for this sample.")
    st.stop()

# Pre-compute display labels & ensure numeric values
metrics_df["metric_label"] = (
    metrics_df["display_label"]
    .fillna(metrics_df["metric_name"])
    .fillna(metrics_df["metric_id"])
)
metrics_df["value_number"] = pd.to_numeric(
    metrics_df["value_number"], errors="coerce"
)

# ---------------------------------------------------------------------------
# Identify runs this sample belongs to (sorted newest-first)
# ---------------------------------------------------------------------------

runs_for_sample = (
    metrics_df[["run_id", "day_id", "run_description",
                 "platform_id", "instrument_name", "instrument_model",
                 "library_id", "library_name", "library_type",
                 "sex", "clinical_test", "registration_date", "sample_type"]]
    .drop_duplicates()
    .sort_values("day_id", ascending=False)
)

run_ids = runs_for_sample["run_id"].tolist()

st.caption(
    f"Sample **{sample_option}** found in **{len(run_ids)}** run(s): "
    + ", ".join(run_ids)
)


# ---------------------------------------------------------------------------
# Helper: render content for a single run
# ---------------------------------------------------------------------------

def render_run_tab(run_id, run_metrics_df, run_info, show_metrics_table=False, show_sample_card=True):
    """Render the detail card, metrics table and chart for one run."""

    left_col, right_col = st.columns(2)

    # ---------------------------------------------------------------
    # LEFT – detail card + metrics table
    # ---------------------------------------------------------------
    with left_col:
        # --- Sample info card (sex, virtual panel) - only show if requested ---
        if show_sample_card:
            sample_card = st.container(border=True)
            sample_card.write(f"**Sample ID:** {sample_option}")

            sex = run_info.get("sex", "")
            if pd.notna(sex) and str(sex).strip():
                sample_card.write(f"**Sex:** {sex}")

            vpanel = run_info.get("clinical_test", "")
            if pd.notna(vpanel) and str(vpanel).strip():
                sample_card.write(f"**Method:** {vpanel}")

            # Registry date if available
            reg_date = run_info.get("registration_date", "")
            if pd.notna(reg_date) and str(reg_date).strip():
                sample_card.write(f"**Registered:** {reg_date}")
        
            # Sample type if available
            sample_type = run_info.get("sample_type", "")
            if pd.notna(sample_type) and str(sample_type).strip():
                sample_card.write(f"**Sample Type:** {sample_type}")

        # --- Run detail card ---
        container = st.container(border=True)
        container.write(f"**Run:** {run_id}  ·  {run_info.get('day_id', '–')}")
        container.write(f"**Platform:** {run_info.get('platform_id', '–')}")
        container.write(f"**Instrument:** {run_info.get('instrument_name', '–')}")

        lib_name = run_info.get("library_name", "")
        if pd.notna(lib_name) and str(lib_name).strip():
            lib_type = run_info.get("library_type", "")
            lib_display = lib_name
            if pd.notna(lib_type) and str(lib_type).strip():
                lib_display += f" ({lib_type})"
            container.write(f"**Library:** {lib_display}")

        # Show metrics table if requested (single run case)
        if show_metrics_table:
            st.write("**Metrics for this run:**")
            metrics_table = run_metrics_df[["metric_label", "value_number"]].drop_duplicates().set_index("metric_label")
            st.dataframe(metrics_table, use_container_width=True)

        # --- Available dimensions for this run ---
        available_metrics = sorted(
            run_metrics_df["metric_label"].dropna().unique().tolist()
        )


    # ---------------------------------------------------------------
    # RIGHT – density plots (library cohort) for up to 4 metrics
    # ---------------------------------------------------------------
    with right_col:
        metric_choices = st.multiselect(
            "Select Metrics to plot (up to 4):",
            available_metrics,
            default=[],
            max_selections=4,
            key=f"dist_metric_{run_id}",
        )

        if metric_choices:
            # --- Determine library for this sample/run ---
            lib_id = run_info.get("library_id") if hasattr(run_info, "get") else run_info.get("library_id", None)
            lib_name = run_info.get("library_name", "")

            if pd.isna(lib_id) or not str(lib_id).strip():
                st.info("No library assigned for this sample/run — cannot show cohort distribution.")
            else:
                # Fetch all samples with the same library in this run
                cohort_df = queries.get_sample_qc_metrics_by_library(engine, str(lib_id))
                cohort_df["metric_label"] = (
                    cohort_df["display_label"]
                    .fillna(cohort_df["metric_name"])
                    .fillna(cohort_df["metric_id"])
                )
                cohort_df["value_number"] = pd.to_numeric(
                    cohort_df["value_number"], errors="coerce"
                )

                # Arrange plots in a 2-column grid
                n_metrics = len(metric_choices)
                grid_cols = 2 if n_metrics > 1 else 1
                cols = st.columns(grid_cols)

                for idx, metric_choice in enumerate(metric_choices):
                    col = cols[idx % grid_cols]

                    # Filter to selected metric
                    cohort_metric = cohort_df[
                        cohort_df["metric_label"] == metric_choice
                    ].copy()

                    with col:
                        if cohort_metric.empty:
                            st.info(f"No cohort data for **{metric_choice}**.")
                            continue

                        n_samples = cohort_metric["sample_id"].nunique()
                        lib_display = lib_name if pd.notna(lib_name) and str(lib_name).strip() else str(lib_id)
                        st.caption(
                            f"**{metric_choice}** · {n_samples} samples · "
                            f"library {lib_display}"
                        )

                        # Current sample's values
                        sample_vals = cohort_metric[
                            cohort_metric["sample_id"] == sample_option
                        ].copy()

                        # Overlaid density – excluding current sample
                        cohort_for_density = cohort_metric[
                            cohort_metric["sample_id"] != sample_option
                        ].copy()
                        
                        density_chart = (
                            alt.Chart(cohort_for_density)
                            .transform_density(
                                density="value_number",
                                as_=["value", "density"]
                            )
                            .mark_area(opacity=0.35)
                            .encode(
                                x=alt.X("value:Q", title=metric_choice),
                                y=alt.Y("density:Q", title=None),
                            )
                        )

                        rule_chart = (
                            alt.Chart(sample_vals)
                            .mark_rule(strokeDash=[6, 3], strokeWidth=2)
                            .encode(
                                x=alt.X("value_number:Q"),
                                color=alt.Color("run_id:N", title="Run"),
                                tooltip=[
                                    alt.Tooltip("value_number:Q", title=metric_choice, format=".2f"),
                                    alt.Tooltip("run_id:N", title="Run")
                                ],
                            )
                        )

                        chart = (density_chart + rule_chart).properties(height=220)
                        st.altair_chart(chart, use_container_width=True)

# ---------------------------------------------------------------------------
# Render: flat layout (no tabs) - single run or multiple runs
# ---------------------------------------------------------------------------

if len(run_ids) == 1:
    # Single run: show metrics table
    rid = run_ids[0]
    run_info = runs_for_sample[runs_for_sample["run_id"] == rid].iloc[0]
    run_data = metrics_df[metrics_df["run_id"] == rid]
    render_run_tab(rid, run_data, run_info, show_metrics_table=True)
else:
    # Multiple runs: show sample info, last run card, comparison table on left, plots on right
    
    # Get last run (first in sorted list since sorted by day_id descending)
    last_run_info = runs_for_sample.iloc[0]
    last_run_id = last_run_info["run_id"]
    
    st.divider()
    
    # Two-column layout: cards + comparison table (left) and plots (right)
    left_col, right_col = st.columns(2)
    
    with left_col:
        # Show sample info card
        sample_card = st.container(border=True)
        sample_card.write(f"**Sample ID:** {sample_option}")

        sex = runs_for_sample.iloc[0].get("sex", "")
        if pd.notna(sex) and str(sex).strip():
            sample_card.write(f"**Sex:** {sex}")

        vpanel = runs_for_sample.iloc[0].get("clinical_test", "")
        if pd.notna(vpanel) and str(vpanel).strip():
            sample_card.write(f"**Method:** {vpanel}")

        reg_date = runs_for_sample.iloc[0].get("registration_date", "")
        if pd.notna(reg_date) and str(reg_date).strip():
            sample_card.write(f"**Registered:** {reg_date}")

        sample_type = runs_for_sample.iloc[0].get("sample_type", "")
        if pd.notna(sample_type) and str(sample_type).strip():
            sample_card.write(f"**Sample Type:** {sample_type}")
        
        # Show last run card
        last_run_card = st.container(border=True)
        last_run_card.write(f"**Run (Latest):** {last_run_id}  ·  {last_run_info.get('day_id', '–')}")
        last_run_card.write(f"**Platform:** {last_run_info.get('platform_id', '–')}")
        last_run_card.write(f"**Instrument:** {last_run_info.get('instrument_name', '–')}")

        lib_name = last_run_info.get("library_name", "")
        if pd.notna(lib_name) and str(lib_name).strip():
            lib_type = last_run_info.get("library_type", "")
            lib_display = lib_name
            if pd.notna(lib_type) and str(lib_type).strip():
                lib_display += f" ({lib_type})"
            last_run_card.write(f"**Library:** {lib_display}")
        
        # Optional expander for other runs
        if len(run_ids) > 1:
            with st.expander(f"Show info for other {len(run_ids) - 1} run(s)"):
                for idx, (_, row) in enumerate(runs_for_sample.iloc[1:].iterrows()):
                    rid = row["run_id"]
                    other_card = st.container(border=True)
                    other_card.write(f"**Run:** {rid}  ·  {row.get('day_id', '–')}")
                    other_card.write(f"**Platform:** {row.get('platform_id', '–')}")
                    other_card.write(f"**Instrument:** {row.get('instrument_name', '–')}")
                    
                    lib_name = row.get("library_name", "")
                    if pd.notna(lib_name) and str(lib_name).strip():
                        lib_type = row.get("library_type", "")
                        lib_display = lib_name
                        if pd.notna(lib_type) and str(lib_type).strip():
                            lib_display += f" ({lib_type})"
                        other_card.write(f"**Library:** {lib_display}")
        
        st.subheader("Metric Comparison")
        
        # Create pivot table: metrics vs runs
        pivot_df = metrics_df.pivot_table(
            index="metric_label",
            columns="run_id",
            values="value_number",
            aggfunc="first"
        )
        
        # Round numeric values for readability
        pivot_df = pivot_df.round(3)
        st.dataframe(pivot_df, use_container_width=True)
    
    with right_col:
        
        # Get last run data
        last_run_data = metrics_df[metrics_df["run_id"] == last_run_id]
        available_metrics = sorted(
            last_run_data["metric_label"].dropna().unique().tolist()
        )
        
        metric_choices = st.multiselect(
            "Select Metrics to plot (up to 4):",
            available_metrics,
            default=[],
            max_selections=4,
            key="multi_run_dist_metric",
        )

        if metric_choices:
            # --- Determine library for this sample/run ---
            lib_id = last_run_info.get("library_id")
            lib_name = last_run_info.get("library_name", "")

            if pd.isna(lib_id) or not str(lib_id).strip():
                st.info("No library assigned for this sample/run — cannot show cohort distribution.")
            else:
                # Fetch all samples with the same library in this run
                cohort_df = queries.get_sample_qc_metrics_by_library(engine, str(lib_id))
                cohort_df["metric_label"] = (
                    cohort_df["display_label"]
                    .fillna(cohort_df["metric_name"])
                    .fillna(cohort_df["metric_id"])
                )
                cohort_df["value_number"] = pd.to_numeric(
                    cohort_df["value_number"], errors="coerce"
                )

                # Arrange plots in a 2-column grid
                n_metrics = len(metric_choices)
                grid_cols = 2 if n_metrics > 1 else 1
                cols = st.columns(grid_cols)

                for idx, metric_choice in enumerate(metric_choices):
                    col = cols[idx % grid_cols]

                    # Filter to selected metric
                    cohort_metric = cohort_df[
                        cohort_df["metric_label"] == metric_choice
                    ].copy()

                    with col:
                        if cohort_metric.empty:
                            st.info(f"No cohort data for **{metric_choice}**.")
                            continue

                        n_samples = cohort_metric["sample_id"].nunique()
                        lib_display = lib_name if pd.notna(lib_name) and str(lib_name).strip() else str(lib_id)
                        st.caption(
                            f"**{metric_choice}** · {n_samples} samples · "
                            f"library {lib_display}"
                        )

                        # Current sample's values across all runs
                        sample_vals = cohort_metric[
                            cohort_metric["sample_id"] == sample_option
                        ].copy()

                        # Overlaid density – excluding current sample
                        cohort_for_density = cohort_metric[
                            cohort_metric["sample_id"] != sample_option
                        ].copy()
                        
                        density_chart = (
                            alt.Chart(cohort_for_density)
                            .transform_density(
                                density="value_number",
                                as_=["value", "density"]
                            )
                            .mark_area(opacity=0.35)
                            .encode(
                                x=alt.X("value:Q", title=metric_choice),
                                y=alt.Y("density:Q", title=None),
                            )
                        )

                        # Rule chart with color by run_id (one line per run)
                        rule_chart = (
                            alt.Chart(sample_vals)
                            .mark_rule(strokeDash=[6, 3], strokeWidth=2)
                            .encode(
                                x=alt.X("value_number:Q"),
                                color=alt.Color("run_id:N", title="Run"),
                                tooltip=[
                                    alt.Tooltip("value_number:Q", title=metric_choice, format=".2f"),
                                    alt.Tooltip("run_id:N", title="Run")
                                ],
                            )
                        )

                        chart = (density_chart + rule_chart).properties(height=220)
                        st.altair_chart(chart, use_container_width=True)
