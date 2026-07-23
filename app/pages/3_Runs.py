
"""Runs page – individual run detail, metrics table, and density distribution plot."""

import streamlit as st
import pandas as pd
import altair as alt

from db import get_engine
import queries
from constants import COLUMN_LABELS, DEFAULT_METRICS_BY_PLATFORM

st.set_page_config(page_title="Runs", layout="wide")

st.write("# Runs")

engine = get_engine()

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

# Fetch run metadata joined with sequencing_chemistry and instruments tables
runs_df = queries.get_runs_with_chemistry(engine)

if runs_df.empty:
    st.warning("No sequencing runs found in the database.")
    st.stop()

# Fetch long-format QC metrics and map metric IDs to human-readable labels
metrics_df = queries.get_sequencing_metrics(engine)

# Rename DB column names to user-friendly labels (e.g. run_id → Run ID)
runs_df = runs_df.rename(columns=COLUMN_LABELS)

# Use DB-driven display_label directly; fall back to metric_name then metric_id
metrics_df["metric_label"] = (
    metrics_df["display_label"]
    .fillna(metrics_df["metric_name"])
    .fillna(metrics_df["metric_id"])
)

# Build lookup: metric_label → platform_id so we can later filter metrics
# to only those relevant for the selected run's sequencing platform
metric_platform_lookup = (
    metrics_df[["metric_label", "metric_platform_id"]]
    .drop_duplicates("metric_label")
    .set_index("metric_label")["metric_platform_id"]
    .to_dict()
)

# Pivot metrics from long format (one row per metric) to wide format
# (one column per metric) so each run has all its metrics in a single row
metrics_pivot = (
    metrics_df.pivot_table(
        index=["run_id", "day_id"],
        columns="metric_label",
        values="value_number",
        aggfunc="first",
    )
    .reset_index()
)

# Merge pivoted metrics into the run metadata dataframe
runs_with_metrics = runs_df.merge(
    metrics_pivot,
    left_on=["Run ID", "Day ID"],
    right_on=["run_id", "day_id"],
    how="left",
)

# Collect all available metric column names (excludes join keys)
metrics_columns = [
    col
    for col in metrics_pivot.columns
    if col not in {"run_id", "day_id"}
]

# Build the run selector list sorted by most recent first
runs_ids = runs_df[["Run ID", "Day ID"]].drop_duplicates().sort_values(
    by=["Run ID", "Day ID"], ascending=False
)

# ---------------------------------------------------------------------------
# Layout: left = run detail, right = distribution chart
# ---------------------------------------------------------------------------

left_column, right_column = st.columns(2)

with left_column:
    # --- Run selector ---
    run_option = st.selectbox(
        "Select Run:",
        runs_ids["Run ID"],
        index=None,
        placeholder="Write run ID...",
    )

    if run_option is None:
        st.write("Please select a Run ID to see the details.")
    elif run_option not in runs_ids["Run ID"].values:
        st.write("Run ID not found in the database. Please select a valid Run ID.")
    else:
        # ---------------------------------------------------------------
        # Selected run data extraction
        # ---------------------------------------------------------------

        selected_row = runs_ids[runs_ids["Run ID"] == run_option].iloc[0]
        selected_run_id = selected_row["Run ID"]
        selected_day_id = selected_row["Day ID"]

        # Subset run metadata to the selected run
        selected_run_df = runs_df[
            (runs_df["Run ID"] == selected_run_id)
            & (runs_df["Day ID"] == selected_day_id)
        ].copy()

        if selected_run_df.empty:
            st.error("Run data could not be loaded. Please try another run.")
            st.stop()

        # Subset long-format QC metrics to the selected run
        selected_metrics_df = metrics_df[
            (metrics_df["run_id"] == selected_run_id)
            & (metrics_df["day_id"] == selected_day_id)
        ].copy()
        selected_metrics_df["metric_label"] = selected_metrics_df["metric_label"].fillna(
            selected_metrics_df["metric_id"]
        )

        # ---------------------------------------------------------------
        # Run detail card – metadata + chemistry info
        # ---------------------------------------------------------------

        container = st.container(border=True)
        container.write(f"**Run Description:** {selected_run_df['Run Description'].values[0]}")
        container.write(f"**Day ID:** {selected_run_df['Day ID'].values[0]}")
        container.write(f"**Instrument Name:** {selected_run_df['Instrument Name'].values[0]}")
        # Show chemistry name resolved from the sequencing_chemistry look-up table
        if "Chemistry Name" in selected_run_df.columns:
            chem_name = selected_run_df["Chemistry Name"].values[0]
            if pd.notna(chem_name) and str(chem_name).strip():
                container.write(f"**Chemistry:** {chem_name}")
        container.write(f"**Number of Samples:** {selected_run_df['Number of Samples'].values[0]}")
        container.write(f"**Number of Cycles:** {selected_run_df['Number of Cycles'].values[0]}")

        # ---------------------------------------------------------------
        # Sequencing metrics table
        # ---------------------------------------------------------------

        st.subheader("Sequencing metrics")
        if selected_metrics_df.empty:
            st.info("No sequencing metrics found for this run.")
        else:
            # Show a clean 3-column table: Metric / Value / Unit
            df_metrics = selected_metrics_df[["metric_label", "value_number", "unit"]].copy()
            df_metrics = df_metrics.rename(
                columns={"metric_label": "Metric", "value_number": "Value", "unit": "Unit"}
            )
            df_metrics["Value"] = pd.to_numeric(df_metrics["Value"], errors="coerce").round(2)
            st.dataframe(df_metrics, use_container_width=True, hide_index=True)

        

with right_column:
    # -------------------------------------------------------------------
    # Facet-wrapped density distribution plots for all platform metrics
    # -------------------------------------------------------------------

    if run_option is not None and run_option in runs_ids["Run ID"].values:
        # Only show default metrics for the selected run's platform
        selected_platform = selected_run_df["Platform"].values[0]
        default_metrics_for_platform = DEFAULT_METRICS_BY_PLATFORM.get(selected_platform, [])
        platform_metrics = [
            col for col in default_metrics_for_platform
            if col in metrics_columns
        ]

        # -----------------------------------------------------------
        # Comparable runs – same description, instrument model, and
        # sequencing chemistry as the selected run
        # -----------------------------------------------------------

        df_same_description = runs_with_metrics[
            runs_with_metrics["Run Description"] == selected_run_df["Run Description"].values[0]
        ]
        # Further narrow to same instrument model
        mask = (
            df_same_description["Instrument Model"] == selected_run_df["Instrument Model"].values[0]
        )
        # Further narrow to same Sequencing Chemistry ID (if available)
        if "Sequencing Chemistry ID" in df_same_description.columns and "Sequencing Chemistry ID" in selected_run_df.columns:
            ref_chem = selected_run_df["Sequencing Chemistry ID"].values[0]
            if pd.notna(ref_chem):
                mask = mask & (df_same_description["Sequencing Chemistry ID"] == ref_chem)
        df_same_instrument_chemistry = df_same_description[mask]

        if df_same_instrument_chemistry.empty:
            st.info("No comparable runs found for this instrument model and chemistry.")
        else:
            # Melt the wide-format metrics into long format for faceting.
            # Each row: Run ID | Day ID | metric | value
            melt_cols = [
                m for m in platform_metrics
                if m in df_same_instrument_chemistry.columns
            ]
            if not melt_cols:
                st.info("No sequencing metrics available to plot.")
            else:
                df_long = df_same_instrument_chemistry.melt(
                    id_vars=["Run ID", "Day ID"],
                    value_vars=melt_cols,
                    var_name="metric",
                    value_name="value",
                )
                df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
                df_long = df_long.dropna(subset=["value"])

                # Build a dataframe of selected-run values for the red rule
                selected_values = df_long[
                    (df_long["Run ID"] == selected_run_id)
                    & (df_long["Day ID"] == selected_day_id)
                ][["metric", "value"]].drop_duplicates()

                # Count comparable runs (for caption)
                n_comparable = df_same_instrument_chemistry["Run ID"].nunique()

                if df_long.empty:
                    st.info("No metric values available to plot.")
                else:
                    st.subheader("Metric distributions")

                    # Merge selected-run marker into the long dataframe so
                    # both layers share a single data source (required for facet).
                    df_long["is_selected"] = False
                    selected_values["is_selected"] = True
                    df_all = pd.concat([df_long, selected_values], ignore_index=True)

                    # KDE density area, faceted by metric with independent axes
                    density_chart = (
                        alt.Chart(df_all)
                        .transform_filter("datum.is_selected === false")
                        .transform_density(
                            "value",
                            as_=["value", "density"],
                            groupby=["metric"],
                        )
                        .mark_area(opacity=0.6)
                        .encode(
                            x=alt.X("value:Q", title=None),
                            y=alt.Y("density:Q", title=None),
                        )
                    )

                    # Red vertical rules for the selected run
                    vlines = (
                        alt.Chart(df_all)
                        .transform_filter("datum.is_selected === true")
                        .mark_rule(color="red", strokeWidth=2)
                        .encode(
                            x=alt.X("value:Q"),
                            tooltip=[alt.Tooltip("value:Q", title="Selected run")],
                        )
                    )

                    # Layer density + rule, then facet-wrap by metric
                    chart = (
                        alt.layer(density_chart, vlines, data=df_all)
                        .properties(width=220, height=160)
                        .facet(
                            facet=alt.Facet("metric:N", title=None),
                            columns=2,
                        )
                        .resolve_scale(x="independent", y="independent")
                    )

                    st.altair_chart(chart, use_container_width=True)

                    st.caption(
                        f"Each panel shows the distribution across **{n_comparable}** comparable runs "
                        f"(same instrument model and sequencing chemistry). "
                        f"The red line marks the selected run **{selected_run_id}**."
                    )
    else:
        st.write("Select a run to see metric distribution plots.")
