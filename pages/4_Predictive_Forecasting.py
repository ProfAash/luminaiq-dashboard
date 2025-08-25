# pages/4_Predictive_Forecasting.py
import numpy as np
import pandas as pd
import streamlit as st
from db import list_uploads_for_user
from sklearn.linear_model import LinearRegression

# Plotly optional
try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

# Kaleido (for PNG export) optional
try:
    import plotly.io as pio  # requires kaleido for static image export
    from io import BytesIO
    HAS_KALEIDO = True
except Exception:
    HAS_KALEIDO = False

st.set_page_config(page_title="Forecasting • LuminaIQ", page_icon="🔮", layout="wide")

# ---------- Auth ----------
user = st.session_state.get("user")
if not user:
    st.warning("Please sign in from the Home page.")
    st.stop()

st.title("🔮 Predictive Forecasting (Baseline)")

# ---------- Dataset picker ----------
uploads = list_uploads_for_user(user_id=user["id"])
if not uploads:
    st.info("Upload a dataset first.")
    st.stop()

options = {f"{u['uploaded_at']} — {u['filename']}": u for u in uploads}
choice = st.selectbox("Choose a dataset", list(options.keys()))
ds = options[choice]

# ---------- Load ----------
path = ds.get("path", "")
try:
    df = pd.read_csv(path)
except Exception as e:
    st.error(f"Could not read dataset: {e}")
    st.stop()

# ---------- Find/create date cols (accept 'Year') ----------
def find_date_cols(df: pd.DataFrame):
    name_hits = [c for c in df.columns if any(k in c.lower() for k in ("date", "day", "time", "year"))]
    dtype_hits = list(df.select_dtypes(include=["datetime", "datetimetz"]).columns)
    cols = list(dict.fromkeys(name_hits + dtype_hits))

    # If 'Year' exists and is integer-like, synthesize YYYY-01-01
    for c in cols:
        if "year" in c.lower():
            try:
                y = df[c].astype("Int64").dropna().astype(int)
                if (y.between(1000, 3000)).all():
                    df["__date_from_year__"] = pd.to_datetime(
                        df[c].astype(int).astype(str) + "-01-01", errors="coerce"
                    )
                    return df, ["__date_from_year__"]
            except Exception:
                pass

    # Coerce likely date columns
    for c in name_hits:
        if c not in dtype_hits:
            try:
                df[c] = pd.to_datetime(df[c], errors="coerce")
            except Exception:
                pass

    date_like = list(df.select_dtypes(include=["datetime", "datetimetz"]).columns)
    return df, date_like

df, date_cols = find_date_cols(df)
num_cols = df.select_dtypes("number").columns.tolist()

if not date_cols or not num_cols:
    st.warning("Need at least one 'date'-like column and one numeric column.")
    st.stop()

date_col = st.selectbox("Date column", date_cols, index=0)
target_col = st.selectbox("Target (numeric)", num_cols, index=0)

# ---------- Frequency & horizon ----------
freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "MS"}
freq_name = st.selectbox("Forecast frequency", list(freq_map.keys()), index=0)
freq = freq_map[freq_name]
max_periods = 365 if freq == "D" else (52 if freq == "W" else 24)
periods = st.slider(
    "Forecast periods",
    7 if freq == "D" else 8,
    max_periods,
    30 if freq == "D" else 12
)

# ---------- Prep ----------
df = df.dropna(subset=[date_col, target_col]).copy()
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col]).sort_values(date_col)

# Reindex evenly by the selected frequency to stabilize baseline trend
df = df.set_index(date_col).resample(freq).sum(numeric_only=True).reset_index()

# Simple linear-trend baseline
df["t"] = np.arange(len(df))
X = df[["t"]].values
y = df[target_col].values
model = LinearRegression().fit(X, y)

# ---------- Forecast ----------
last_t = df["t"].iloc[-1]
future_t = np.arange(last_t + 1, last_t + periods + 1).reshape(-1, 1)
yhat = model.predict(future_t)

future_dates = pd.date_range(
    start=df[date_col].iloc[-1] + pd.tseries.frequencies.to_offset(freq),
    periods=periods,
    freq=freq
)
forecast_df = pd.DataFrame({date_col: future_dates, target_col: yhat, "type": "forecast"})
hist_df = df[[date_col, target_col]].copy()
hist_df["type"] = "history"
both = pd.concat([hist_df, forecast_df], ignore_index=True)

# ---------- Backtest (MAPE) ----------
def mape(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    denom = np.clip(np.abs(y_true), 1e-9, None)
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)

with st.expander("Advanced (Backtest)", False):
    do_bt = st.checkbox("Evaluate last 20% (MAPE)")
    if do_bt and len(df) > 10:
        n = max(1, int(len(df) * 0.2))
        train, test = df.iloc[:-n].copy(), df.iloc[-n:].copy()
        train["t"] = np.arange(len(train))
        test["t"]  = np.arange(len(train), len(train) + len(test))
        m = LinearRegression().fit(train[["t"]], train[target_col].values)
        pred = m.predict(test[["t"]])
        st.info(f"MAPE on holdout: **{mape(test[target_col].values, pred):.2f}%**")

# ---------- Plot ----------
if HAS_PLOTLY:
    fig_ts = px.line(both, x=date_col, y=target_col, color="type", title=f"{target_col} forecast ({freq_name})")
    st.plotly_chart(fig_ts, use_container_width=True)

    # Optional PNG export
    if HAS_KALEIDO:
        try:
            buf = BytesIO()
            pio.write_image(fig_ts, buf, format="png", scale=2)  # kaleido required
            st.download_button("Download forecast PNG", buf.getvalue(), "forecast.png", "image/png")
        except Exception as e:
            st.caption(f"PNG export unavailable: {e}")
    else:
        st.caption("Tip: add `kaleido==0.2.1` to requirements.txt to enable PNG export.")
else:
    st.line_chart(both.pivot(index=date_col, columns="type", values=target_col))

# ---------- Download CSV ----------
st.download_button(
    "Download forecast CSV",
    data=forecast_df.to_csv(index=False),
    file_name="forecast.csv",
    mime="text/csv",
)

st.caption("Baseline linear trend with frequency control. For seasonality/holidays, upgrade to Prophet/ARIMA.")
