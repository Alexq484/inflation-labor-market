"""Replicates the SAS OLS model in Python and runs robustness checks.

Input:  data/olsData.csv (monthly FRED / BLS JOLTS data; inflation, WageGrowth and
        oilPriceChange are 12-month % changes computed in the original Excel workbook)
Output: printed regression tables
"""
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.stattools import durbin_watson

df = pd.read_csv("data/olsData.csv", parse_dates=["Date"])
df = df.dropna(subset=["inflation", "WageGrowth", "oilPriceChange"])

formula = "inflation ~ unemploymentRate + JobOpeningsRate + WageGrowth + oilPriceChange"

base = smf.ols(formula, df).fit()
print("=== 1. Baseline OLS (matches SAS) ===")
print(base.summary().tables[1], f"\nN={int(base.nobs)}  R2={base.rsquared:.4f}")
print(f"Durbin-Watson: {durbin_watson(base.resid):.3f}")

nw = smf.ols(formula, df).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
print("\n=== 2. Newey-West standard errors (12 lags) ===")
print(nw.summary().tables[1])

infl = base.get_influence()
cooks = infl.cooks_distance[0]
top = df.assign(cooks=cooks).nlargest(3, "cooks")[["Date", "inflation", "oilPriceChange", "cooks"]]
print("\n=== 3. Most influential observations ===")
print(top.to_string(index=False))

drop = smf.ols(formula, df.drop(index=top.index[0])).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
print("\n=== 4. Without the most influential month (Newey-West SEs) ===")
print(drop.summary().tables[1], f"\nR2={drop.rsquared:.4f}")

df["covid"] = ((df["Date"] >= "2020-03-01") & (df["Date"] <= "2021-12-01")).astype(int)
cov = smf.ols(formula + " + covid", df).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
print("\n=== 5. With COVID indicator (Mar 2020 - Dec 2021 base months, Newey-West SEs) ===")
print(cov.summary().tables[1], f"\nR2={cov.rsquared:.4f}")
