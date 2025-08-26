# components.py
import streamlit as st
from components import kpi

def kpi(label: str, value: str, delta: str | None = None, help: str | None = None):
    """Small wrapper so KPIs look consistent across pages."""
    st.metric(label, value, delta=delta, help=help)


