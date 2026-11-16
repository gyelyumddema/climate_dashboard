
import pandas as pd
from scipy import stats

# The two measures the visitor can choose (label -> column name in the CSV)
MEASURES = {
    "Land (1753-2015)": "LandAverageTemperature",
    "Land and ocean (1850-2015)": "LandAndOceanAverageTemperature",
}
MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


def load_raw(path):
    """Read the CSV and add Year and Month columns (notebook cell 7)."""
    df = pd.read_csv(path)
    df["dt"] = pd.to_datetime(df["dt"])
    df["Year"] = df["dt"].dt.year
    df["Month"] = df["dt"].dt.month
    return df


def make_yearly(df, column):
    """One row per year, keeping only COMPLETE years (all 12 months present),
    then the anomaly = yearly average minus the 1951-1980 average (cells 12 and 13)."""
    yearly = df.groupby("Year").agg(Avg=(column, "mean"), Count=(column, "count")).reset_index()
    yearly = yearly[yearly["Count"] == 12].copy()
    baseline = yearly[(yearly["Year"] >= 1951) & (yearly["Year"] <= 1980)]["Avg"].mean()
    yearly["Anomaly"] = yearly["Avg"] - baseline
    yearly["Decade"] = (yearly["Year"] // 10) * 10
    return yearly, baseline


def trend(yearly, start, end):
    """Straight-line trend for the years start..end (notebook cell 16)."""
    part = yearly[(yearly["Year"] >= start) & (yearly["Year"] <= end)]
    res = stats.linregress(part["Year"], part["Anomaly"])
    return {
        "per_decade": res.slope * 10,   # slope is per year, so x10 gives per decade
        "slope": res.slope,
        "intercept": res.intercept,
        "r": res.rvalue,
        "p": res.pvalue,
        "years": len(part),
    }


def decade_table(yearly):
    """Average anomaly for each decade (notebook cells 15 and 19)."""
    table = yearly.groupby("Decade").agg(
        Mean=("Anomaly", "mean"), Years=("Anomaly", "count"),
        First=("Year", "min"), Last=("Year", "max")).reset_index()
    return table


def period_rates(yearly):
    """Warming rate in three periods, and the z-test between the first and last
    (notebook cells 17 and 24)."""
    first_year = int(yearly["Year"].min())
    periods = [("Before 1950", first_year, 1949), ("1950-1989", 1950, 1989), ("1990-2015", 1990, 2015)]
    rows = []
    for name, start, end in periods:
        part = yearly[(yearly["Year"] >= start) & (yearly["Year"] <= end)]
        res = stats.linregress(part["Year"], part["Anomaly"])
        rows.append({"Period": name, "From": start, "To": end, "Years": len(part),
                     "PerDecade": res.slope * 10, "Slope": res.slope, "StdErr": res.stderr})
    table = pd.DataFrame(rows)
    a, b = rows[0], rows[2]
    # z = (difference between the two slopes) / (combined uncertainty)
    z = (b["Slope"] - a["Slope"]) / (a["StdErr"] ** 2 + b["StdErr"] ** 2) ** 0.5
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return {"table": table, "z": z, "p": p, "times": b["Slope"] / a["Slope"]}


def season_table(df, column):
    """Average temperature of each month in 1850-1949 and in 1990-2015 (notebook cells 22 and 23)."""
    early = df[(df["Year"] >= 1850) & (df["Year"] <= 1949)].groupby("Month")[column].mean()
    late = df[(df["Year"] >= 1990) & (df["Year"] <= 2015)].groupby("Month")[column].mean()
    out = pd.DataFrame({"Early": early, "Late": late})
    out["Diff"] = out["Late"] - out["Early"]
    out["Name"] = MONTH_NAMES
    return out
