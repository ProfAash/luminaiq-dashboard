try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

import pandas as pd
import streamlit as st
from db import list_uploads_for_user

# Try Plotly, fall back to Streamlit charts if not available
try:
    import plotly.express as px
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

st.set_page_config(page_title="Forecasting • LuminaIQ", page_icon="🔮", layout="wide")
user = st.session_state.get("user")
if not user:
    st.warning("Please sign in from the Home page.")
    st.stop()

st.title("🔮 Predictive Forecasting (Baseline)")
uploads = list_uploads_for_user(user_id=user["id"])

if not uploads:
    st.info("Upload a dataset first.")
    st.stop()

options = {f"{u['uploaded_at']} — {u['filename']}": u for u in uploads}
choice = st.selectbox("Choose a dataset", list(options.keys()))
ds = options[choice]

try:
    df = pd.read_csv(ds["path"])
except Exception as e:
    st.error(f"Could not read dataset: {e}")
    st.stop()

date_cols = [c for c in df.columns if "date" in c.lower()]
num_cols = df.select_dtypes("number").columns.tolist()

if not date_cols or not num_cols:
    st.warning("Need at least one 'date'-like column and one numeric column.")
    st.stop()

date_col = st.selectbox("Date column", date_cols, index=0)
target_col = st.selectbox("Target (numeric)", num_cols, index=0)
periods = st.slider("Forecast periods", 7, 90, 30)

df = df.dropna(subset=[date_col, target_col]).copy()
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col])
df = df.sort_values(date_col)

df["t"] = np.arange(len(df))
X = df[["t"]].values.reshape(-1,1)
y = df[target_col].values
model = LinearRegression().fit(X, y)

last_t = df["t"].iloc[-1]
future_t = np.arange(last_t + 1, last_t + periods + 1).reshape(-1,1)
yhat = model.predict(future_t)

future_dates = pd.date_range(start=df[date_col].iloc[-1] + pd.Timedelta(days=1), periods=periods, freq="D")
forecast_df = pd.DataFrame({date_col: future_dates, target_col: yhat, "type": "forecast"})
hist_df = df[[date_col, target_col]].copy()
hist_df["type"] = "history"
both = pd.concat([hist_df, forecast_df], ignore_index=True)

st.plotly_chart(px.line(both, x=date_col, y=target_col, color="type"), use_container_width=True)
st.download_button("Download forecast CSV", data=forecast_df.to_csv(index=False), file_name="forecast.csv", mime="text/csv")
st.caption("Baseline linear trend only. For seasonality/holidays, upgrade to Prophet/ARIMA.")
