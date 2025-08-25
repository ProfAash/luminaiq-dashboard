import streamlit as st

def kpi(label: str, value: str, *, delta: str | None = None, help: str | None = None):
    st.markdown(
        f"""
        <div title="{help or ''}" style="
            padding:14px;border-radius:14px;
            background:rgba(255,255,255,0.03);
            border:1px solid rgba(255,255,255,.08);
            ">
            <div style="opacity:.75;font-size:.85rem">{label}</div>
            <div style="font-size:1.6rem;font-weight:700;margin-top:2px">{value}</div>
            {f'<div style="color:#10B981;margin-top:2px">↗ {delta}</div>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
