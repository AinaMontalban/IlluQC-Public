"""Safe dashboard error reporting."""

import logging

import streamlit as st


def show_data_error(context: str, exc: Exception) -> None:
    """Log diagnostic details and show users a non-sensitive message."""
    logging.exception("%s", context, exc_info=exc)
    st.error(f"{context}. Check the application logs for details.")
