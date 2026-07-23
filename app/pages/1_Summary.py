
import streamlit as st
import pandas as pd
import plotly.express as px

from db import get_engine
from errors import show_data_error
import queries

# Page configuration must be the first Streamlit command in this script.
st.set_page_config(page_title="Activity Summary", layout="wide")
st.header("IlluQC Activity Summary")

engine = get_engine()

# Get list of years based on today's date
start_year = 2020
current_year = pd.Timestamp.today().year
year_list = ["All years"] + list(range(current_year, start_year - 1, -1))

# Using 'with' notation for the sidebar
with st.sidebar:
    st.header("Filters")

    # Option 1: Single Year Selection
    option = st.selectbox(
            "Year",
            year_list,
            index=0,
            key="selected_year",
            help="Filters runs and samples by calendar year.",
        )

    # Option 2: Range Selection
    #start_year, end_year = st.slider("Select Year Range", start_year, current_year, (start_year, current_year))

# Get runs based on selected year and platform
if option == "All years":
    runs_df = queries.get_runs_with_instruments(engine)
    # samples
    samples_df = queries.get_all_samples(engine)
else:
    runs_df = queries.get_runs_with_instruments(engine, year=option)
    samples_df = queries.get_all_samples(engine, year=option)

# Summary subpages
tab1, tab2 = st.tabs(["Runs Summary", "Samples Summary"])

# =========================================================================
# Runs Summary
# =========================================================================
with tab1:
    left_col, middle_col, right_col = st.columns(3)
    with left_col:
        st.subheader("Runs Summary")
        
        platforms_df = queries.get_platforms(engine)
        
        platform_options = ["All platforms"] + sorted(
            platforms_df["platform_id"].dropna().unique().tolist()
        )
        
        platform_option = st.selectbox(
            "Platform",
            platform_options,
            index=0,
            key="selected_platform",
            help="Limits run results to one sequencing platform.",
        )

    if platform_option != "All platforms":
        runs_df = runs_df[runs_df["platform_id"] == platform_option]

    left_column, middle_column, right_column = st.columns(3)
    
    total_runs = runs_df["run_id"].nunique() if not runs_df.empty else 0
    total_samples = int(
        pd.to_numeric(runs_df["num_samples"], errors="coerce").fillna(0).sum()
    ) if not runs_df.empty else 0
    num_protocols = runs_df["run_description"].nunique() if not runs_df.empty else 0

    with left_column:
        st.metric("Total Runs Sequenced", total_runs, border=True)
    with middle_column:
        st.metric("Total Samples Sequenced", total_samples, border=True)
    with right_column:
        st.metric("Number of Protocols", num_protocols, border=True)

    # count the number of rows
    if not runs_df.empty:
        left_column, right_column = st.columns(2)
        with left_column:
            # Prepare data for treemap plot and count number of runs for each run_description
            total_runs_per_run_description = runs_df.groupby('run_description', as_index=False).agg({'run_id': 'size'})
            fig = px.treemap(total_runs_per_run_description, path=['run_description'], values='run_id', title="Protocol Distribution")
            st.plotly_chart(fig)
        with right_column:
            # Create histogram of runs per sequencer
            runs_per_instrument = runs_df['instrument_name'].value_counts()
            fig_bar=px.bar(runs_per_instrument, x=runs_per_instrument.index, y=runs_per_instrument.values, text_auto=True, title="Runs per sequencer")
            # Change x-axis title and y-axis title
            fig_bar.update_layout(xaxis_title="Sequencer", yaxis_title="Number of Runs")
            st.plotly_chart(fig_bar)
    else:
       st.info("No runs found for the selected year.")

# =========================================================================
# Sample Summary
# =========================================================================
with tab2:
    st.subheader("Samples Summary")
    
    try:
        if not samples_df.empty:
            has_dates = not samples_df["registration_date"].isnull().all()
            if has_dates:
                # Convert registration_date to datetime
                samples_df["registration_date"] = pd.to_datetime(samples_df["registration_date"], errors='coerce')
            else:
                st.warning("⚠️ Registration dates not available in sample data. Showing all samples.")
            
            total_samples = samples_df["sample_id"].nunique()
            clinical_method = samples_df["clinical_method"].nunique()
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Samples", total_samples, border=True)

            with col2:
                st.metric("Clinical Methods", clinical_method, border=True)
            
            with col3:
                # Sex distribution pie chart - calculate from samples_df
                sex_counts = samples_df[samples_df['sex'].notna() & (samples_df['sex'] != '')]['sex'].value_counts().reset_index()
                sex_counts.columns = ['sex', 'count']
                
                if not sex_counts.empty:
                    fig_sex = px.pie(
                        sex_counts,
                        values="count",
                        names="sex",
                        title="Sex Distribution"
                    )
                    fig_sex.update_layout(
                        legend=dict(
                            orientation="h",
                            yanchor="top",
                            y=-0.08,
                            xanchor="center",
                            x=0.5,
                        ),
                        height=190,
                        margin=dict(t=35, b=45, l=0, r=0),
                    )
                    st.plotly_chart(fig_sex, use_container_width=True)
            
            left_col, right_col = st.columns(2)
            with left_col:
                top_samples = queries.get_top_repeated_samples(engine, limit=5)
                if not top_samples.empty:
                    st.write("**Top 5 Repeated Samples**")
                    st.dataframe(top_samples)
                else:
                    st.metric("No repeated samples found.", value="", border=True)
                    st.dataframe(pd.DataFrame(columns=["sample_id", "count"]))
                
            with right_col:
                # Create a histogram of sample registration dates
                fig_samples = px.histogram(
                    samples_df,
                    x="registration_date",
                    nbins=20,
                    title="Sample Registration Dates",
                    labels={"registration_date": "Registration Date", "count": "Number of Samples"},
                )
                st.plotly_chart(fig_samples, use_container_width=True)
        else:
            st.info("No data is available for the selected year.")
            
    except Exception as exc:
        show_data_error("Could not load sample summary", exc)
