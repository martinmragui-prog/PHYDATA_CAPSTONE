from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "capstone_clean.csv"
REQUIRED_COLUMNS = {
    "Country Name",
    "Country Code",
    "Year",
    "GDP_per_capita",
    "Log_GDP",
    "Agriculture_GDP",
    "Agriculture_Land",
    "Agri_Group",
    "Land_Group",
}


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def format_currency(value: float) -> str:
    return f"${value:,.0f}" if pd.notna(value) else "Not available"


def spearman_correlation(data: pd.DataFrame, x: str, y: str) -> float:
    pairs = data[[x, y]].dropna()
    if len(pairs) < 2:
        return float("nan")
    return pairs[x].rank().corr(pairs[y].rank())


def show_scatter_chart(
    data: pd.DataFrame,
    *,
    x: str,
    y: str,
    color: str | None = None,
) -> None:
    chart_data = data.dropna(subset=[x, y])
    if chart_data.empty:
        st.info("There are no complete observations for this chart in the current selection.")
        return
    st.scatter_chart(
        chart_data,
        x=x,
        y=y,
        color=color,
        width="stretch",
    )
    st.caption(f"{len(chart_data):,} country-year observations shown.")


st.set_page_config(
    page_title="Agriculture & Income Dashboard",
    page_icon="🌾",
    layout="wide",
)
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {
        background: #f5f8f4;
        border: 1px solid #e5ebe2;
        border-radius: 12px;
        padding: 1rem 1.15rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌾 Agriculture & Income")
st.markdown(
    "An interactive dashboard exploring how the size of a country's agriculture "
    "sector and its agricultural land relate to income over time."
)
st.caption(
    "Research question: Do countries with a larger agriculture share of GDP or "
    "more agricultural land tend to have lower GDP per person?"
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

for column in (
    "Year",
    "GDP_per_capita",
    "Log_GDP",
    "Agriculture_GDP",
    "Agriculture_Land",
):
    data[column] = pd.to_numeric(data[column], errors="coerce")
data = data.dropna(subset=["Year"])
if data.empty:
    st.error("The cleaned data has no valid year values to display.")
    st.stop()
data["Year"] = data["Year"].astype(int)

with st.sidebar:
    st.header("Dashboard filters")
    st.caption("All charts, summaries, and the data table respond to these filters.")
    year_min = int(data["Year"].min())
    year_max = int(data["Year"].max())
    year_selection = st.slider(
        "Year range",
        min_value=year_min,
        max_value=year_max,
        value=(year_min, year_max),
        step=1,
        help="Choose which years to include in the analysis.",
    )
    country_options = sorted(data["Country Name"].dropna().unique().tolist())
    selected_countries = st.multiselect(
        "Countries",
        options=country_options,
        help="Leave empty to include every country.",
    )
    agriculture_groups = sorted(data["Agri_Group"].dropna().unique().tolist())
    selected_agriculture_groups = st.multiselect(
        "Agriculture share groups",
        options=agriculture_groups,
        help="Groups are based on agriculture's share of GDP (low, medium, or high).",
    )
    land_groups = sorted(data["Land_Group"].dropna().unique().tolist())
    selected_land_groups = st.multiselect(
        "Agricultural land groups",
        options=land_groups,
        help="Groups are based on agricultural land as a share of total land area.",
    )
    st.divider()
    st.markdown(
        "**Measure guide**\n"
        "- **GDP per capita:** average economic output per person, in current US dollars.\n"
        "- **Agriculture share:** agriculture, forestry, and fishing value added as a percentage of GDP.\n"
        "- **Agricultural land:** agricultural land as a percentage of total land area."
    )

filtered_data = data[data["Year"].between(*year_selection)].copy()
if selected_countries:
    filtered_data = filtered_data[
        filtered_data["Country Name"].isin(selected_countries)
    ]
if selected_agriculture_groups:
    filtered_data = filtered_data[
        filtered_data["Agri_Group"].isin(selected_agriculture_groups)
    ]
if selected_land_groups:
    filtered_data = filtered_data[filtered_data["Land_Group"].isin(selected_land_groups)]

if filtered_data.empty:
    st.warning("No records match these filters. Adjust the selections in the sidebar.")
    st.stop()

country_count = filtered_data["Country Name"].nunique()
gdp_median = filtered_data["GDP_per_capita"].median()
agriculture_median = filtered_data["Agriculture_GDP"].median()
land_median = filtered_data["Agriculture_Land"].median()

metric_columns = st.columns(4)
metric_columns[0].metric("Country-year records", f"{len(filtered_data):,}")
metric_columns[1].metric("Countries represented", f"{country_count:,}")
metric_columns[2].metric("Median GDP per capita", format_currency(gdp_median))
metric_columns[3].metric(
    "Median agriculture share",
    f"{agriculture_median:.1f}%" if pd.notna(agriculture_median) else "Not available",
)
st.caption(
    f"Selected period: {year_selection[0]}–{year_selection[1]}. "
    f"Median agricultural land in this selection: "
    f"{land_median:.1f}% of land area."
    if pd.notna(land_median)
    else f"Selected period: {year_selection[0]}–{year_selection[1]}. "
    "Agricultural-land values are not available for this selection."
)

overview_tab, relationships_tab, groups_tab, countries_tab, data_tab = st.tabs(
    ["Overview", "Relationships", "Group comparisons", "Country rankings", "Data"]
)

with overview_tab:
    st.subheader("How the indicators change over time")
    st.markdown(
        "Each point summarizes the countries in the current selection for that "
        "year. The median is used so a few exceptionally high-income countries "
        "do not dominate the overall pattern."
    )
    yearly = (
        filtered_data.groupby("Year", as_index=False)
        .agg(
            **{
                "Median GDP per capita (US$)": ("GDP_per_capita", "median"),
                "Median agriculture share (%)": ("Agriculture_GDP", "median"),
                "Median agricultural land (%)": ("Agriculture_Land", "median"),
            }
        )
        .sort_values("Year")
    )
    trend_left, trend_right = st.columns(2)
    with trend_left:
        st.markdown("**GDP per capita**")
        st.caption("Median income per person, measured in current US dollars.")
        gdp_trend = yearly.dropna(subset=["Median GDP per capita (US$)"])
        if gdp_trend.empty:
            st.info("GDP per-capita values are unavailable for this selection.")
        else:
            st.line_chart(
                gdp_trend,
                x="Year",
                y="Median GDP per capita (US$)",
                width="stretch",
            )
    with trend_right:
        st.markdown("**Agriculture's share of GDP**")
        st.caption("Median agriculture-sector contribution as a percentage of GDP.")
        agriculture_trend = yearly.dropna(subset=["Median agriculture share (%)"])
        if agriculture_trend.empty:
            st.info("Agriculture-share values are unavailable for this selection.")
        else:
            st.line_chart(
                agriculture_trend,
                x="Year",
                y="Median agriculture share (%)",
                width="stretch",
            )
    land_trend = yearly.dropna(subset=["Median agricultural land (%)"])
    if land_trend.empty:
        st.info("Agricultural-land values are unavailable for this selection.")
    else:
        st.markdown("**Agricultural land over time**")
        st.caption("Median agricultural land as a percentage of total land area.")
        st.line_chart(
            land_trend,
            x="Year",
            y="Median agricultural land (%)",
            width="stretch",
        )

with relationships_tab:
    st.subheader("Do agriculture and income move together?")
    st.markdown(
        "Each dot is one country in one year. The vertical axis uses the natural "
        "logarithm of GDP per capita (rather than raw dollars) so differences "
        "between lower- and higher-income observations remain visible. A downward "
        "pattern would be consistent with lower income where the agriculture "
        "measure is higher, but it would not show that one causes the other."
    )
    agriculture_pairs = filtered_data.dropna(
        subset=["Agriculture_GDP", "GDP_per_capita"]
    )
    land_pairs = filtered_data.dropna(
        subset=["Agriculture_Land", "GDP_per_capita"]
    )
    agriculture_correlation = spearman_correlation(
        agriculture_pairs, "Agriculture_GDP", "GDP_per_capita"
    )
    land_correlation = spearman_correlation(
        land_pairs, "Agriculture_Land", "GDP_per_capita"
    )
    correlation_left, correlation_right = st.columns(2)
    with correlation_left:
        st.metric(
            "Agriculture share vs GDP per capita",
            f"{agriculture_correlation:+.2f}"
            if pd.notna(agriculture_correlation)
            else "Not available",
            help=(
                f"Spearman rank correlation across {len(agriculture_pairs):,} "
                "country-year records with both values. Near -1 indicates that "
                "higher agriculture shares tend to rank with lower GDP per capita; "
                "near +1 indicates the reverse."
            ),
        )
    with correlation_right:
        st.metric(
            "Agricultural land vs GDP per capita",
            f"{land_correlation:+.2f}"
            if pd.notna(land_correlation)
            else "Not available",
            help=(
                f"Spearman rank correlation across {len(land_pairs):,} "
                "country-year records with both values. Near -1 indicates that "
                "more agricultural land tends to rank with lower GDP per capita; "
                "near +1 indicates the reverse."
            ),
        )
    st.caption(
        "Spearman correlation summarizes the direction and strength of a "
        "monotonic association. Repeated country-year records are not independent, "
        "and correlation does not establish cause and effect."
    )
    relationship_left, relationship_right = st.columns(2)
    with relationship_left:
        st.markdown("**Agriculture share and income**")
        show_scatter_chart(
            filtered_data,
            x="Agriculture_GDP",
            y="Log_GDP",
            color="Agri_Group",
        )
    with relationship_right:
        st.markdown("**Agricultural land and income**")
        show_scatter_chart(
            filtered_data,
            x="Agriculture_Land",
            y="Log_GDP",
            color="Land_Group",
        )
    st.info(
        "Missing values are omitted from each scatter plot. Country-year records "
        "repeat the same countries over time, so dots are not independent samples."
    )

with groups_tab:
    st.subheader("Compare typical income across agriculture groups")
    st.markdown(
        "The bars show median GDP per capita for the selected records in each "
        "group. Group labels are categories from the cleaned dataset; they are "
        "not randomized experiments or evidence of causal effects."
    )
    group_left, group_right = st.columns(2)
    with group_left:
        st.markdown("**By agriculture share of GDP**")
        agriculture_group_summary = (
            filtered_data.dropna(subset=["Agri_Group", "GDP_per_capita"])
            .groupby("Agri_Group")["GDP_per_capita"]
            .median()
            .sort_values()
        )
        if agriculture_group_summary.empty:
            st.info("No group and GDP values are available for this selection.")
        else:
            st.bar_chart(
                agriculture_group_summary,
                horizontal=True,
                x_label="Median GDP per capita (US$)",
                y_label="Agriculture share group",
                width="stretch",
            )
    with group_right:
        st.markdown("**By agricultural-land share**")
        land_group_summary = (
            filtered_data.dropna(subset=["Land_Group", "GDP_per_capita"])
            .groupby("Land_Group")["GDP_per_capita"]
            .median()
            .sort_values()
        )
        if land_group_summary.empty:
            st.info("No group and GDP values are available for this selection.")
        else:
            st.bar_chart(
                land_group_summary,
                horizontal=True,
                x_label="Median GDP per capita (US$)",
                y_label="Agricultural land group",
                width="stretch",
            )
    st.caption(
        "A group median describes the middle observed country-year value; it does "
        "not mean every country in that group has a similar income."
    )

with countries_tab:
    st.subheader("Countries with the highest and lowest median incomes")
    st.markdown(
        "Rankings use each country's median GDP per capita across the selected "
        "years. They are useful for comparing this filtered period, not for "
        "measuring a country's growth or overall wellbeing."
    )
    country_medians = (
        filtered_data.dropna(subset=["GDP_per_capita"])
        .groupby("Country Name")["GDP_per_capita"]
        .median()
        .sort_values(ascending=False)
    )
    if country_medians.empty:
        st.info("GDP per-capita values are unavailable for this selection.")
    else:
        ranking_left, ranking_right = st.columns(2)
        with ranking_left:
            st.markdown("**Highest median GDP per capita**")
            st.bar_chart(
                country_medians.head(10).sort_values(),
                horizontal=True,
                x_label="Median GDP per capita (US$)",
                y_label="Country",
                width="stretch",
            )
        with ranking_right:
            st.markdown("**Lowest median GDP per capita**")
            st.bar_chart(
                country_medians.tail(10).sort_values(ascending=False),
                horizontal=True,
                x_label="Median GDP per capita (US$)",
                y_label="Country",
                width="stretch",
            )

with data_tab:
    st.subheader("Explore the filtered country-year records")
    st.markdown(
        "A row represents one country in one year. Blank cells mean an indicator "
        "was not reported for that country-year; charts exclude blanks only for "
        "the measure(s) they use."
    )
    st.dataframe(
        filtered_data.sort_values(["Country Name", "Year"]),
        hide_index=True,
        width="stretch",
    )
    completeness = (
        filtered_data[
            ["GDP_per_capita", "Agriculture_GDP", "Agriculture_Land"]
        ]
        .notna()
        .sum()
        .rename(
            {
                "GDP_per_capita": "GDP per capita",
                "Agriculture_GDP": "Agriculture share",
                "Agriculture_Land": "Agricultural land",
            }
        )
    )
    st.markdown("**Available observations by indicator**")
    st.bar_chart(
        completeness,
        x_label="Country-year records with a value",
        width="stretch",
    )

st.divider()
st.caption(
    "Data source: World Bank World Development Indicators. These charts describe "
    "associations, not cause and effect. Countries appear in multiple years, and "
    "indicator coverage varies across countries and time."
)
