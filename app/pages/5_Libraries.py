"""Libraries page – visualize library protocols and usage."""

import streamlit as st
import pandas as pd
import altair as alt

from db import get_engine
import queries

st.set_page_config(page_title="Libraries", layout="wide")
st.write("# Libraries")

engine = get_engine()

# --- Load library table ---
libraries_df = None
try:
    libraries_df = pd.read_sql_query("SELECT * FROM library", engine)
except Exception as e:
    st.error(f"Could not load libraries table: {e}")

if libraries_df is None or libraries_df.empty:
    st.warning("No libraries found in the database.")
    st.stop()


# ---------------------------------------------------------------------------
# Sample metrics over time (by library)
# ---------------------------------------------------------------------------

st.header("Sample metrics over time (by library)")

# Let the user pick one or more libraries to explore
lib_options = libraries_df.set_index("library_id")["library_name"].to_dict()
selected_libs = st.multiselect(
    "Select library(ies):",
    options=list(lib_options.keys()),
    format_func=lambda x: f"{x} — {lib_options.get(x)}",
    default=[list(lib_options.keys())[0]] if lib_options else [],
)

if not selected_libs:
    st.info("Choose at least one library to explore sample metrics over time.")
else:
    # Fetch sample QC metrics for selected libraries across runs
    try:
        df = queries.get_sample_qc_metrics_by_libraries(engine, selected_libs)
    except Exception as e:
        st.error(f"Could not load sample metrics for selected libraries: {e}")
        df = pd.DataFrame()

    if df.empty:
        st.info("No sample QC metrics found for the selected library(ies).")
    else:
        # Resolve metric labels and numeric values
        df["metric_label"] = df["display_label"].fillna(df["metric_name"]).fillna(df["metric_id"])
        df["value_number"] = pd.to_numeric(df["value_number"], errors="coerce")
        df["day_dt"] = pd.to_datetime(df["day_id"], errors="coerce")

        # Metric selection
        available_metrics = sorted(df["metric_label"].dropna().unique().tolist())
        sel_metric = st.selectbox("Select a sample metric:", available_metrics)

        if sel_metric:
            plot_df = df[df["metric_label"] == sel_metric].copy()


            # Simple box plot for each run
            box_plot = alt.Chart(plot_df).mark_boxplot().encode(
                x=alt.X("run_id:N", title="Run"),
                y=alt.Y("value_number:Q", title="Value", scale=alt.Scale(zero=False))
            )

            points = alt.Chart(plot_df).mark_point(size=60, opacity=0.6).encode(
                x=alt.X("run_id:N", title="Run"),
                y=alt.Y("value_number:Q", scale=alt.Scale(zero=False)),
                tooltip=[
                    alt.Tooltip("sample_id:N"),
                    alt.Tooltip("run_id:N"),
                    alt.Tooltip("value_number:Q", format=".3f")
                ]
            )

            base = (box_plot + points)

            chart = base.properties(height=400, width=800)
            st.altair_chart(chart, use_container_width=True)

            st.caption("Box plot shows distribution per run. Individual dots represent samples.")

            # ------- Density plot -------
            st.subheader("Density Distribution")
            
            # Create density plot
            density_chart = (
                alt.Chart(plot_df)
                .transform_density(
                    density="value_number",
                    as_=["value", "density"]
                )
                .mark_area(opacity=0.5, color="steelblue")
                .encode(
                    x=alt.X("value:Q", title=sel_metric),
                    y=alt.Y("density:Q", title="Density"),
                )
                .properties(height=300, width=800)
            )
            
            st.altair_chart(density_chart, use_container_width=True)
            st.caption("Density plot shows overall distribution of the metric across all selected libraries and runs.")
