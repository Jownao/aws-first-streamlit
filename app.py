import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import os

# ----------------------------------
# Page config
# ----------------------------------
st.set_page_config(
    page_title="Uber Pickups | AWS EC2 + S3",
    layout="wide"
)

st.title("🚕 Uber Pickups in NYC")
st.caption(
    "This Streamlit app runs on an AWS EC2 instance and consumes a dataset "
    "directly from Amazon S3."
)

# ----------------------------------
# Constants
# ----------------------------------
DATE_COLUMN = "date/time"
DATA_URL = "https://s3-jownao.s3.us-east-1.amazonaws.com/uber-raw-data-sep14.csv.gz"

MAPBOX_TOKEN = os.getenv("MAPBOX_API_KEY")

# ----------------------------------
# Data loading
# ----------------------------------
@st.cache_data
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows)
    data.columns = [c.lower() for c in data.columns]
    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    return data

# ----------------------------------
# Sidebar
# ----------------------------------
st.sidebar.header("Controls")

rows = st.sidebar.slider(
    "Number of rows to load",
    min_value=10_000,
    max_value=1_000_000,
    step=50_000,
    value=100_000
)

data = load_data(rows)

selected_base = st.sidebar.multiselect(
    "Select Uber Base",
    options=sorted(data["base"].unique()),
    default=list(data["base"].unique())
)

hour = st.sidebar.slider("Hour of day", 0, 23, 17)

filtered_data = data[
    (data["base"].isin(selected_base)) &
    (data[DATE_COLUMN].dt.hour == hour)
]

# ----------------------------------
# KPIs
# ----------------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Records Loaded", f"{len(data):,}")
col2.metric("Unique Uber Bases", data["base"].nunique())
col3.metric(
    "Date Range",
    f"{data[DATE_COLUMN].min().date()} → {data[DATE_COLUMN].max().date()}"
)

# ----------------------------------
# Histogram
# ----------------------------------
st.subheader("📊 Pickups Distribution by Hour")

hist_values = np.histogram(
    data[DATE_COLUMN].dt.hour,
    bins=24,
    range=(0, 24)
)[0]

st.bar_chart(hist_values)

# ----------------------------------
# Map / Heatmap
# ----------------------------------
st.subheader(f"🗺️ Pickup Locations at {hour}:00")

map_style = "mapbox://styles/mapbox/dark-v10" if MAPBOX_TOKEN else None

st.pydeck_chart(
    pdk.Deck(
        map_style=map_style,
        initial_view_state=pdk.ViewState(
            latitude=40.73,
            longitude=-73.93,
            zoom=10,
            pitch=45,
        ),
        layers=[
            pdk.Layer(
                "HeatmapLayer",
                data=filtered_data,
                get_position="[lon, lat]",
                radius_pixels=60,
                opacity=0.8,
            ),
        ],
    )
)

# ----------------------------------
# Raw data
# ----------------------------------
with st.expander("📄 Show raw data"):
    st.dataframe(filtered_data.head(1000))
