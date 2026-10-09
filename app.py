from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "capstone_clean.csv"
FIGURES_DIR = PROJECT_DIR / "figures"
REQUIRED_COLUMNS = {
    "Country Name",
    "Country Code",
    "Year",
    "GDP_per_capita",
    "Agriculture_GDP",
    "Agriculture_Land",
    "Agri_Group",
    "Land_Group",
}
CHARTS = [
    (
        "GDP and agriculture share",
        "chart1_gdp_vs_agriculture_share.png",
        "GDP per person compared with agriculture's share of GDP.",
    ),
    (
        "GDP and agricultural land",
        "chart2_gdp_by_land_group.png",
        "GDP per person across low, medium, and high agricultural-land groups.",
    ),
    (
        "Agriculture share over time",
        "chart3_agriculture_share_over_time.png",
        "Median agriculture share of GDP by year, with 2000 marked.",
    ),
]


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


st.set_page_config(page_title="Agriculture and Income", layout="wide")
st.title("Agriculture and Income")
st.markdown(
    "Explore how agriculture's share of the economy and agricultural land relate "
    "to GDP per person across countries and years."
)

if not DATA_PATH.is_file():
    st.error(f"Cleaned data file not found: {DATA_PATH.name}")
    st.stop()

data = load_data(str(DATA_PATH))
missing_columns = REQUIRED_COLUMNS.difference(data.columns)
if missing_columns:
    st.error(
        "The cleaned data is missing required columns: "
        + ", ".join(sorted(missing_columns))
    )
    st.stop()

if data.empty:
    st.error("The cleaned data file has no rows to display.")
    st.stop()

year_min = int(data["Year"].min())
year_max = int(data["Year"].max())
year_selection = st.slider(
    "Year range",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max),
    step=1,
)
country_options = sorted(data["Country Name"].dropna().unique().tolist())
selected_countries = st.multiselect(
    "Countries",
    options=country_options,
    help="Leave this empty to include all countries.",
)

filtered_data = data[data["Year"].between(*year_selection)]
if selected_countries:
    filtered_data = filtered_data[
        filtered_data["Country Name"].isin(selected_countries)
    ]

country_count = filtered_data["Country Name"].nunique()
metric_columns = st.columns(3)
metric_columns[0].metric("Country-year records", f"{len(filtered_data):,}")
metric_columns[1].metric("Countries", f"{country_count:,}")
metric_columns[2].metric("Years selected", f"{year_selection[0]}–{year_selection[1]}")

st.subheader("Charts")
st.caption(
    "These charts are the saved figures from the notebook analysis. "
    "The filters above apply to the summary and data table, not to the figures."
)
chart_tabs = st.tabs([chart[0] for chart in CHARTS])
for tab, (_, filename, caption) in zip(chart_tabs, CHARTS):
    chart_path = FIGURES_DIR / filename
    with tab:
        if not chart_path.is_file():
            st.error(f"Chart image not found: figures/{filename}")
        else:
            st.image(str(chart_path), caption=caption, width="stretch")

st.subheader("Filtered cleaned data")
st.dataframe(
    filtered_data.sort_values(["Country Name", "Year"]),
    hide_index=True,
    width="stretch",
)

st.info(
    "These charts show relationships, not cause and effect. Countries appear in "
    "multiple years, so country-year observations are not independent."
)
