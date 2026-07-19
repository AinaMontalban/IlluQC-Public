"""Shared database engine for the Streamlit app."""

import os
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


@st.cache_resource
def get_engine():
    """Return a cached SQLAlchemy engine built from environment variables.

    Reads database credentials from environment variables set by docker-compose.
    If the connection cannot be established the app shows a friendly error
    message and stops execution.
    """
    # Read from environment variables (set by docker-compose)
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "ngsqcdb")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")

    if not all([db_host, db_port, db_name, db_user, db_password]):
        st.error(
            "**Database credentials not found.**  "
            "Make sure these environment variables are set: "
            "`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`"
        )
        st.stop()

    url = (
        f"postgresql+psycopg2://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    engine = create_engine(url)

    # Verify the connection is reachable
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        st.error(
            f"🗄️ **Cannot connect to the database.**  \n"
            f"`{db_host}:{db_port}/{db_name}` — {exc}"
        )
        st.stop()

    return engine
