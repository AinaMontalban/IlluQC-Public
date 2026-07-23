"""About IlluQC."""

import os

import streamlit as st
from sqlalchemy import text

from db import get_engine


st.set_page_config(page_title="About IlluQC", layout="wide")

st.title("About IlluQC")

st.write(
    "IlluQC is a quality-control tool for storing, exploring, and visualising "
    "sequencing run and sample metrics."
)

st.write(f"**IlluQC version:** `{os.getenv('ILLUQC_VERSION', '0.1.0')}`")

engine = get_engine()
with engine.connect() as connection:
    database_version = connection.execute(
        text("SELECT value FROM schema_metadata WHERE key = 'schema_version'")
    ).scalar_one_or_none()

st.write(f"**Database version:** `{database_version or 'Unknown'}`")

st.caption("IlluQC · NGS quality control")
