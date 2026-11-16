"""
Climate Change Trends dashboard (Streamlit).
Run it with:   streamlit run app.py
The calculations live in analysis.py, this file only shows them.
"""
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from analysis import (MEASURES, MONTH_NAMES, decade_table, load_raw, make_yearly,
                      period_rates, season_table, trend)

BLUE = "#2A78D6"    # cooler / earlier
ORANGE = "#EB6834"  # warmer / recent


st.set_page_config(page_title="Climate Change Trends", layout="wide")

# custom css for founts
custom_css = """
<style>
/* Apply Times New Roman globally to main text, headings, and widgets */
html, body, [class*="css"], .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, li, label, .stMetricValue, .stMetricLabel {
    font-family: 'Times New Roman', Times, serif !important;
    color: #111111 !important; 
}

/* Make sure general text is a bit larger */
html, body, [class*="css"] {
    font-size: 18px !important; 
}

/* Specific adjustments for markdown paragraphs to increase line height for readability */
.stMarkdown p, .stMarkdown li {
    font-size: 19px !important;
    line-height: 1.6 !important;
}

/* Make tab text larger and bold */
.stTabs [data-baseweb="tab"] {
    font-size: 20px !important;
    font-weight: 600 !important;
    color: #111111 !important;
    font-family: 'Times New Roman', Times, serif !important;
}

/* Make metric cards larger */
div[data-testid="stMetricValue"] > div {
    font-size: 32px !important;
    color: #111111 !important;
    font-family: 'Times New Roman', Times, serif !important;
}
div[data-testid="stMetricLabel"] > div {
    font-size: 18px !important;
    color: #333333 !important; 
    font-family: 'Times New Roman', Times, serif !important;
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    font-family: 'Times New Roman', Times, serif !important;
    font-size: 18px !important;
    color: #111111 !important;
}

/* Info/Warning/Success boxes text */
.stAlert p {
    font-size: 18px !important;
    color: #111111 !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


@st.cache_data
def get_data():
    """Read the CSV once and remember it, so the page stays fast."""
    return load_raw(Path(__file__).parent / "GlobalTemperatures.csv")


df = get_data()

#sidebar
st.sidebar.header("Choose what to explore")
measure_label = st.sidebar.radio("Measure", list(MEASURES))
column = MEASURES[measure_label]

yearly, baseline = make_yearly(df, column)
first_year, last_year = int(yearly["Year"].min()), int(yearly["Year"].max())

year_range = st.sidebar.slider("Years shown in the trend chart", first_year, last_year,
                               (first_year, last_year), key="years_" + column)
st.sidebar.caption(
    "Land: 263 complete years from 1753. Land and ocean: 166 complete years from 1850, "
    "because ocean data does not exist before then.")

#  numbers used everywhere
overall = trend(yearly, first_year, last_year)
rates = period_rates(yearly)
decades = decade_table(yearly)
seasons = season_table(df, column)
warmest = decades.loc[decades["Mean"].idxmax()]
best_month = int(seasons["Diff"].idxmax())

# header
st.title("Climate Change Trends")
st.write("How has the temperature of the Earth's land changed over 266 years of records, "
         "and is it warming faster now? Source: Berkeley Earth, 1750 to 2015.")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Warming rate", f"{overall['per_decade']:+.3f} °C per decade",
          help=f"Straight-line trend, {first_year} to {last_year}")
k2.metric("1990-2015 vs before 1950", f"{rates['times']:.1f}x faster")
k3.metric("Warmest decade", f"{int(warmest['Decade'])}s",
          f"{warmest['Mean']:+.2f} °C vs 1951-1980", delta_color="off")
k4.metric("Month that warmed most", MONTH_NAMES[best_month - 1],
          f"{seasons.loc[best_month, 'Diff']:+.2f} °C", delta_color="off")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. Trend", "2. Decades", "3. Warming speed", "4. Seasons", "Conclusions", "Data and method"])

#tab 1: trend
with tab1:
    st.subheader("How has temperature changed over time?")
    st.write("Each point is one year. The anomaly shows how far that year was from the 1951-1980 "
             "average: above the dashed zero line is warmer, below is cooler. "
             "The dashed dark line is the straight-line trend for the years you chose in the sidebar.")
    start, end = year_range
    if end - start < 4:
        st.warning("Please choose at least 5 years in the sidebar.")
    else:
        part = yearly[(yearly["Year"] >= start) & (yearly["Year"] <= end)]
        t = trend(yearly, start, end)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=part["Year"], y=part["Anomaly"], mode="lines", name="Yearly anomaly",
            line=dict(color=BLUE, width=2),
            hovertemplate="%{x}<br>Anomaly: %{y:+.2f} °C<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=[start, end],
            y=[t["intercept"] + t["slope"] * start, t["intercept"] + t["slope"] * end],
            mode="lines", name="Trend line", line=dict(color="#555555", width=2, dash="dash"),
            hoverinfo="skip"))
        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        fig.update_layout(title=f"Global {measure_label.split(' (')[0].lower()} temperature anomaly, "
                                f"{start}-{end} (baseline 1951-1980)",
                          xaxis_title="Year", yaxis_title="Anomaly (°C)",
                          hovermode="x", height=430, margin=dict(t=60, b=40))
        st.plotly_chart(fig, use_container_width=True)
        significant = "statistically significant" if t["p"] < 0.05 else "not statistically significant"
        p_text = "p < 0.001" if t["p"] < 0.001 else f"p = {t['p']:.3f}"
        st.info(f"**{t['per_decade']:+.3f} °C per decade** for {start}-{end} ({t['years']} years). "
                f"r = {t['r']:.2f}, {p_text}: {significant}.")
        if t["years"] < 20:
            st.caption("Short ranges are noisy. Treat this rate with care.")
        with st.expander("Show the yearly values as a table"):
            st.dataframe(part[["Year", "Avg", "Anomaly"]].round(3), hide_index=True)

#  tab 2: decades
with tab2:
    st.subheader("Which decades were the warmest?")
    st.write("Each bar is the average anomaly of one decade. Blue bars are cooler than "
             "1951-1980 and orange bars are warmer. Hover over a bar to see the exact value.")
    colors = [ORANGE if v >= 0 else BLUE for v in decades["Mean"]]
    opacity = [1.0 if n == 10 else 0.6 for n in decades["Years"]]
    fig = go.Figure(go.Bar(
        x=decades["Decade"], y=decades["Mean"], marker=dict(color=colors, opacity=opacity),
        customdata=decades[["First", "Last", "Years"]].values,
        hovertemplate="%{x}s (%{customdata[0]}-%{customdata[1]}, %{customdata[2]} years)"
                      "<br>Average anomaly: %{y:+.2f} °C<extra></extra>"))
    fig.add_hline(y=0, line_dash="dot", line_color="grey")
    fig.update_layout(title=f"Average temperature anomaly by decade, {first_year}-{last_year} "
                            "(baseline 1951-1980)",
                      xaxis_title="Decade", yaxis_title="Anomaly (°C)", height=430,
                      xaxis=dict(tickmode="linear", dtick=20, ticksuffix="s"),
                      margin=dict(t=60, b=40))
    st.plotly_chart(fig, use_container_width=True)
    partial = decades[decades["Years"] < 10]
    notes = [f"{int(r.Decade)}s ({int(r.First)}-{int(r.Last)} only)" for r in partial.itertuples()]
    st.caption("Lighter bars are partial decades: " + " and ".join(notes) + ".")
    with st.expander("Show the decade values as a table"):
        st.dataframe(decades.rename(columns={"Mean": "Average anomaly (°C)"}).round(2), hide_index=True)

# tab 3: warming speed
with tab3:
    st.subheader("Is warming faster now than before?")
    st.write("We measured how fast temperature rose in three periods, in degrees Celsius per decade, "
             "then used a z-test to check whether the first and last rates really differ.")
    left, right = st.columns([3, 2])
    table = rates["table"]
    with left:
        fig = go.Figure(go.Bar(
            x=[f"{r.Period}<br>({r.From}-{r.To})" for r in table.itertuples()],
            y=table["PerDecade"], marker=dict(color=ORANGE, opacity=[0.55, 0.78, 1.0]),
            text=[f"{v:+.3f}" for v in table["PerDecade"]], textposition="outside",
            hovertemplate="%{x}<br>%{y:.3f} °C per decade<extra></extra>"))
        fig.update_layout(title="Warming rate by period (°C per decade)",
                          yaxis_title="°C per decade", height=420, margin=dict(t=60, b=40),
                          yaxis=dict(range=[0, table["PerDecade"].max() * 1.2]))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        a, b = table.iloc[0], table.iloc[2]
        st.metric("Recent rate compared with the first period", f"{rates['times']:.1f}x faster")
        st.write(f"The rate rose from {a['PerDecade']:.3f} °C per decade ({a['From']}-{a['To']}) "
                 f"to {b['PerDecade']:.3f} °C per decade (1990-2015).")
        st.write(f"**z-test:** z = {rates['z']:.2f}, p about {rates['p']:.1e}.")
        if abs(rates["z"]) > 1.96:
            st.success("z is beyond ±1.96, so p is below 0.05. We reject the null hypothesis "
                       "that the two rates are equal. The difference is significant.")
        else:
            st.warning("z is within ±1.96, so we cannot say the rates differ.")
    with st.expander("Show the rates as a table"):
        st.dataframe(table[["Period", "From", "To", "Years", "PerDecade"]]
                     .rename(columns={"PerDecade": "°C per decade"}).round(3), hide_index=True)

#  tab 4: seasons
with tab4:
    st.subheader("Do some seasons warm more than others?")
    st.write("The left chart compares the average temperature of each month in 1850-1949 with "
             "1990-2015. The right chart shows how much warmer each month has become.")
    month_name = st.selectbox("Pick a month", MONTH_NAMES, index=best_month - 1)
    chosen = MONTH_NAMES.index(month_name) + 1
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=seasons["Name"].str[:3], y=seasons["Early"], mode="lines+markers",
                                 name="1850-1949", line=dict(color=BLUE, width=2)))
        fig.add_trace(go.Scatter(x=seasons["Name"].str[:3], y=seasons["Late"], mode="lines+markers",
                                 name="1990-2015", line=dict(color=ORANGE, width=2)))
        fig.update_layout(title="Average temperature by month (°C)", yaxis_title="Temperature (°C)",
                          hovermode="x unified", height=400, margin=dict(t=60, b=40),
                          legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        opacity = [1.0 if m == chosen else 0.55 for m in seasons.index]
        fig = go.Figure(go.Bar(
            x=seasons["Name"].str[:3], y=seasons["Diff"], marker=dict(color=ORANGE, opacity=opacity),
            hovertemplate="%{x}: %{y:+.2f} °C warmer<extra></extra>"))
        fig.update_layout(title="How much warmer each month is now (°C)", yaxis_title="Difference (°C)",
                          height=400, margin=dict(t=60, b=40))
        st.plotly_chart(fig, use_container_width=True)
    row = seasons.loc[chosen]
    st.info(f"**{month_name}: {row['Diff']:+.2f} °C.** "
            f"{row['Early']:.2f} °C in 1850-1949 and {row['Late']:.2f} °C in 1990-2015.")
    with st.expander("Show the monthly values as a table"):
        st.dataframe(seasons[["Name", "Early", "Late", "Diff"]].rename(
            columns={"Name": "Month", "Early": "1850-1949", "Late": "1990-2015",
                     "Diff": "Difference"}).round(2), hide_index=True)

# tab 5: conclusions
with tab5:
    st.subheader("What the data tells us")
    a, b, c = st.columns(3)
    with a:
        st.markdown("#### Long-term trend")
        st.markdown(
            "- Land temperature has risen about **0.047 °C per decade** across 1753-2015 (r = 0.63). "
            "Land and ocean together has risen about 0.054 °C per decade since 1850.\n"
            "- The rise is not steady. Land warmed 0.023 °C per decade before 1950, 0.086 from 1950 to "
            "1989 and 0.274 from 1990 to 2015.\n"
            "- All three hypotheses were supported: an upward trend, different rates in different "
            "periods, and a positive link between year and temperature.")
    with b:
        st.markdown("#### Where warming is strongest")
        st.markdown(
            "- The most pronounced warming is recent. Every decade since the 1980s is warmer than the "
            "one before it, and the 2010s are the warmest in the record.\n"
            "- The 1990-2015 rate is about 12 times the early rate on land, and about 5 times on land "
            "and ocean.\n"
            "- On land, winter and early spring warmed most. March rose by 1.40 °C and July by 0.74 °C, "
            "comparing 1990-2015 with 1850-1949.")
    with c:
        st.markdown("#### Recommendations")
        st.markdown(
            "- **Keep monitoring.** This file stops in 2015. Add newer years to check whether the "
            "faster rate continues.\n"
            "- **Go local.** Repeat the analysis with country-level data to see what the trend means "
            "for individual countries, such as Bhutan.\n"
            "- **Build awareness.** Share the seasonal findings with communities that depend on the "
            "seasons, such as farming, water and snow. Our data cannot show those effects, so they "
            "need their own data.")

# tab 6: data and method
with tab6:
    st.subheader("How we cleaned and tested the data")
    a, b = st.columns(2)
    with a:
        st.markdown("#### Cleaning steps")
        st.markdown(
            "1. Loaded 3,192 monthly rows (January 1750 to December 2015) and 9 columns.\n"
            "2. Found 12 missing land values, all in 1750-1752, and 1,200 missing values in other "
            "columns before 1850. We did not fill them in.\n"
            "3. Found no duplicate rows and no impossible values (a maximum below the average, or a "
            "minimum above it).\n"
            "4. Kept only years with all 12 months: 263 land years (1753-2015) and 166 land-and-ocean "
            "years (1850-2015).\n"
            f"5. Turned each year into an anomaly by subtracting the 1951-1980 average "
            f"({baseline:.3f} °C for the measure you selected).")
        st.markdown("#### Limits")
        st.markdown(
            "- Early records are less certain. The average uncertainty was 3.38 °C in the 1750s and "
            "0.91 °C by the 1840s.\n"
            "- A trend shows that temperature rose, not why.\n"
            "- Yearly temperatures are linked to the year before, so very small p-values look stronger "
            "than they should.\n"
            "- The data ends in 2015 and is global only.")
    with b:
        st.markdown("#### Words used on this page")
        st.markdown(
            "- **Anomaly:** how far a year is from the 1951-1980 average.\n"
            "- **°C per decade:** the slope of the trend line multiplied by 10.\n"
            "- **r:** how close the points sit to the trend line, from -1 to 1.\n"
            "- **p-value:** how likely results this strong would be if nothing were really happening. "
            "Below 0.05 is called significant.\n"
            "- **z-test:** a test of whether two rates differ by more than chance. Beyond ±1.96 is "
            "significant at the 0.05 level.")
    with st.expander("Show the first rows of the raw data"):
        st.dataframe(df.head(24), hide_index=True)
    st.caption("Source: Berkeley Earth Surface Temperature Study, via Kaggle (GlobalTemperatures.csv)."
               "     PRG405-Introduction to Data Science, Samtse College of Education.")