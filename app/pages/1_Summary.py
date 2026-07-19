
import streamlit as st
import pandas as pd
import plotly.express as px

from db import get_engine
import queries

engine = get_engine()

# Set page configuration
st.set_page_config(page_title="Summary", layout="wide")

# Add year selector
st.title("Summary")


# Get list of years based on today's date
start_year = 2020
current_year = pd.Timestamp.today().year
year_list = ["All years"] + list(range(current_year, start_year - 1, -1))

# Create selectors side by side
col1, col2 = st.columns(2)

with col1:
    option = st.selectbox(
        "Select Year:",
        year_list,
        index=0,
        placeholder="Select year...",
        key="selected_year",
    )

with col2:
    platforms_df = queries.get_platforms(engine)
    platform_options = ["All platforms"] + platforms_df["platform_id"].dropna().tolist()
    platform_option = st.selectbox(
        "Select Platform:",
        platform_options,
        index=0,
        placeholder="Select platform...",
        key="selected_platform",
    )

# View selector in sidebar
view_option = st.sidebar.radio(
    "Select View:",
    options=["Both", "Runs Summary Only", "Samples Summary Only"],
    horizontal=False,
    index=0
)

if option == "All years":
    runs_df = queries.get_runs_with_instruments(engine)
else:
    runs_df = queries.get_runs_with_instruments(engine, year=option)

if platform_option != "All platforms":
    runs_df = runs_df[runs_df["platform_id"] == platform_option]

st.divider()

# Split page based on view option
if view_option == "Both":
    left_col, right_col = st.columns(2)
elif view_option == "Runs Summary Only":
    left_col = st.container()
    right_col = None
else:  # Samples Summary Only
    left_col = None
    right_col = st.container()

# =========================================================================
# LEFT COLUMN: Runs Summary
# =========================================================================
if view_option in ["Both", "Runs Summary Only"] and left_col is not None:
    with left_col:
        st.subheader("Runs Summary")
        
        left_column, middle_column, right_column = st.columns(3)

        # Runs sequenced in the selected year
        if not runs_df.empty:
            with left_column:
                total_runs = runs_df['run_id'].nunique()
                st.metric("Total Runs Sequenced", total_runs, border=True)

            with middle_column:
                # Samples sequenced in the selected year
                total_samples = runs_df['num_samples'].sum()
                st.metric("Total Samples Sequenced", total_samples, border=True)

            with right_column:
                # Number of distinct protocols
                num_protocols = runs_df['run_description'].nunique()
                st.metric("Number of Protocols", num_protocols, border=True)

        # count the number of rows
        if not runs_df.empty:
            # Prepare data for treemap plot and count number of runs for each run_description
            total_runs_per_run_description = runs_df.groupby('run_description', as_index=False).agg({'run_id': 'size'})
            fig = px.treemap(total_runs_per_run_description, path=['run_description'], values='run_id', title="Protocol Distribution")
            st.plotly_chart(fig, use_container_width=True)

            # Create histogram of runs per sequencer
            runs_per_instrument = runs_df['instrument_name'].value_counts()

            fig_bar=px.bar(runs_per_instrument, x=runs_per_instrument.index, y=runs_per_instrument.values, text_auto=True, title="Runs per sequencer")

            # Change x-axis title and y-axis title
            fig_bar.update_layout(xaxis_title="Sequencer", yaxis_title="Number of Runs")

            st.plotly_chart(fig_bar, use_container_width=True)

        else:
            st.info("No runs found for the selected year.")

# =========================================================================
# RIGHT COLUMN: Sample Summary
# =========================================================================
if view_option in ["Both", "Samples Summary Only"] and right_col is not None:
    with right_col:
        st.subheader("Sample Summary")
        
        try:
            # Check if registration_date is available
            all_samples = queries.get_all_samples(engine)
            has_dates = (
                "registration_date" in all_samples.columns 
                and all_samples["registration_date"].notna().any()
            )
            
            # Filter by year if selected
            if option != "All years":
                samples_df = queries.get_all_samples(engine, year=option)
            else:
                samples_df = all_samples
            
            if not samples_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    total_samples = samples_df['sample_id'].nunique()
                    st.metric(
                        "Total Samples",
                        total_samples,
                        border=True
                    )
                
                with col2:
                    clinical_test = samples_df['clinical_test'].nunique()
                    st.metric(
                        "Clinical Tests",
                        clinical_test,
                        border=True
                    )
                
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
                    st.plotly_chart(fig_sex, use_container_width=True)
                
                # Top repeated samples
                try:
                    top_samples = queries.get_top_repeated_samples(engine, limit=10)
                    if not top_samples.empty:
                        st.write("**Top 10 Repeated Samples**")
                        st.dataframe(top_samples, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not load top samples: {e}")
                
                # Show warning below pie chart if dates not available
                if not has_dates:
                    st.warning("⚠️ Registration dates not available in sample data. Showing all samples.")
            else:
                st.warning("No sample data found for the selected year.")
                
        except Exception as e:
            st.error(f"Could not load sample summary: {e}")

