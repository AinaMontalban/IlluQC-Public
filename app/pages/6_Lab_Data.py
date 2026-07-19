"""Reference Data page – view instruments, sequencing chemistry, and libraries."""

import streamlit as st
import pandas as pd

from db import get_engine

st.set_page_config(page_title="Reference Data", layout="wide")
st.write("# Reference Data")

engine = get_engine()

# Create tabs for each reference table
tab1, tab2, tab3, tab4 = st.tabs(["Instruments", "Sequencing Chemistry", "Libraries", "Metrics"])

# =============================================================================
# Tab 1: Instruments
# =============================================================================

with tab1:
    st.subheader("Sequencing Instruments")
    st.write("All registered sequencing instruments in the database.")
    
    try:
        instruments_df = pd.read_sql_query(
            "SELECT instrument_id, instrument_name, instrument_model, instrument_type, platform_id FROM instruments ORDER BY platform_id, instrument_id",
            engine
        )
        
        if instruments_df.empty:
            st.info("No instruments found in the database.")
        else:
            # Display summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Instruments", len(instruments_df))
            with col2:
                platforms = instruments_df["platform_id"].nunique()
                st.metric("Platforms", platforms)
            with col3:
                types = instruments_df["instrument_type"].nunique()
                st.metric("Instrument Types", types)
            
            # Display table
            st.dataframe(instruments_df, use_container_width=True, hide_index=True)
            
            # Platform breakdown
            st.subheader("Instruments by Platform")
            platform_counts = instruments_df["platform_id"].value_counts().reset_index()
            platform_counts.columns = ["Platform", "Count"]
            st.bar_chart(data=platform_counts.set_index("Platform"), use_container_width=True)
            
    except Exception as e:
        st.error(f"Could not load instruments table: {e}")


# =============================================================================
# Tab 2: Sequencing Chemistry
# =============================================================================

with tab2:
    st.subheader("Sequencing Chemistry Kits")
    st.write("All sequencing chemistry kits/flowcells registered in the database.")
    
    try:
        chemistry_df = pd.read_sql_query(
            "SELECT sequencing_chemistry_id, chemistry_name, platform_id FROM sequencing_chemistry ORDER BY platform_id, sequencing_chemistry_id",
            engine
        )
        
        if chemistry_df.empty:
            st.info("No sequencing chemistry kits found in the database.")
        else:
            # Display summary statistics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Chemistry Kits", len(chemistry_df))
            with col2:
                platforms = chemistry_df["platform_id"].nunique()
                st.metric("Platforms", platforms)
            
            # Display table
            st.dataframe(chemistry_df, use_container_width=True, hide_index=True)
            
            # Platform breakdown
            st.subheader("Chemistry Kits by Platform")
            platform_counts = chemistry_df["platform_id"].value_counts().reset_index()
            platform_counts.columns = ["Platform", "Count"]
            st.bar_chart(data=platform_counts.set_index("Platform"), use_container_width=True)
            
    except Exception as e:
        st.error(f"Could not load sequencing chemistry table: {e}")


# =============================================================================
# Tab 3: Libraries
# =============================================================================

with tab3:
    st.subheader("Library Protocols")
    st.write("All sequencing library preparation kits registered in the database.")
    
    try:
        libraries_df = pd.read_sql_query(
            "SELECT library_id, library_name, library_version, library_type FROM library ORDER BY library_id",
            engine
        )
        
        if libraries_df.empty:
            st.info("No libraries found in the database.")
        else:
            # Display summary statistics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Libraries", len(libraries_df))
            with col2:
                if "library_type" in libraries_df.columns:
                    types = libraries_df["library_type"].nunique()
                    st.metric("Library Types", types)
            
            # Display table
            st.dataframe(libraries_df, use_container_width=True, hide_index=True)
            
            # Library type distribution
            if "library_type" in libraries_df.columns and not libraries_df["library_type"].isna().all():
                st.subheader("Libraries by Type")
                type_counts = libraries_df["library_type"].value_counts().reset_index()
                type_counts.columns = ["Library Type", "Count"]
                st.bar_chart(data=type_counts.set_index("Library Type"), use_container_width=True)
            
    except Exception as e:
        st.error(f"Could not load libraries table: {e}")


# =============================================================================
# Tab 4: QC Metrics Definitions
# =============================================================================

with tab4:
    st.subheader("Registered QC Metrics")
    st.write("All QC metrics registered in the database schema.")
    
    try:
        metrics_df = pd.read_sql_query(
            """SELECT 
                metric_id, 
                metric_name, 
                display_label, 
                workflow_step, 
                scope, 
                unit, 
                value_type, 
                platform_id,
                description 
            FROM qc_metric_definitions 
            ORDER BY workflow_step, scope, metric_id""",
            engine
        )
        
        if metrics_df.empty:
            st.info("No QC metrics found in the database.")
        else:
            # Display summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Metrics", len(metrics_df))
            with col2:
                workflows = metrics_df["workflow_step"].nunique()
                st.metric("Workflow Steps", workflows)
            with col3:
                scopes = metrics_df["scope"].nunique()
                st.metric("Scopes", scopes)
            with col4:
                platforms = metrics_df["platform_id"].nunique()
                st.metric("Platforms", platforms)
            
            # Display table
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
            
            # Metrics by workflow step
            if "workflow_step" in metrics_df.columns:
                st.subheader("Metrics by Workflow Step")
                step_counts = metrics_df["workflow_step"].value_counts().reset_index()
                step_counts.columns = ["Workflow Step", "Count"]
                st.bar_chart(data=step_counts.set_index("Workflow Step"), use_container_width=True)
            
            # Metrics by scope
            if "scope" in metrics_df.columns:
                st.subheader("Metrics by Scope")
                scope_counts = metrics_df["scope"].value_counts().reset_index()
                scope_counts.columns = ["Scope", "Count"]
                st.bar_chart(data=scope_counts.set_index("Scope"), use_container_width=True)
            
    except Exception as e:
        st.error(f"Could not load QC metrics table: {e}")
