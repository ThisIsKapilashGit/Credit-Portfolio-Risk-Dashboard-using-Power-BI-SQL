"""
Credit Portfolio Risk Dashboard
EDA & KPI Summary — generates summary stats and charts
Usage:  python eda_kpi.py
Requires: pandas, matplotlib, seaborn
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from pathlib import Path

DATA = Path("data")
OUT  = Path("data/charts")
OUT.mkdir(exist_ok=True)

sns.set_theme(style="darkgrid", palette="muted")
plt.rcParams.update({"figure.dpi": 120, "font.family": "DejaVu Sans"})

# ── load ──────────────────────────────────────────────────────────────────────
print("Loading datasets …")
loans    = pd.read_csv(DATA / "loans.csv",    parse_dates=["disbursement_date","maturity_date","npa_since_date"])
borrowers= pd.read_csv(DATA / "borrowers.csv",parse_dates=["date_of_birth","customer_since"])
products = pd.read_csv(DATA / "loan_products.csv")
snaps    = pd.read_csv(DATA / "loan_monthly_snapshot.csv", parse_dates=["snapshot_month"])
branches = pd.read_csv(DATA / "branches.csv")

df = (loans
      .merge(products[["product_id","product_category"]], on="product_id", how="left")
      .merge(borrowers[["borrower_id","credit_score","annual_income","employment_status","state"]], on="borrower_id", how="left")
      .merge(branches[["branch_code","region"]], on="branch_code", how="left"))

active = df[df["loan_status"].isin(["Active","Restructured"])]

# ── KPI Summary ───────────────────────────────────────────────────────────────
total_portfolio = active["outstanding_balance"].sum()
gross_npa       = active.loc[active["npa_flag"]==1, "outstanding_balance"].sum()
npa_ratio       = gross_npa / total_portfolio * 100
npa_count       = active["npa_flag"].sum()
avg_cs          = borrowers["credit_score"].mean()

print("\n" + "="*55)
print("  CREDIT PORTFOLIO – KEY PERFORMANCE INDICATORS")
print("="*55)
print(f"  Total Active Loans      : {len(active):>12,}")
print(f"  Total Portfolio (₹)     : {total_portfolio:>15,.0f}")
print(f"  Gross NPA (₹)           : {gross_npa:>15,.0f}")
print(f"  Gross NPA Ratio         : {npa_ratio:>11.2f} %")
print(f"  NPA Loan Count          : {npa_count:>12,}")
print(f"  Avg Borrower Credit Score: {avg_cs:>10.1f}")
print("="*55)

# ── Chart 1 : NPA Ratio by Product Category ───────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
cat_npa = (active.groupby("product_category")
           .apply(lambda x: x.loc[x["npa_flag"]==1,"outstanding_balance"].sum()
                            / x["outstanding_balance"].sum() * 100)
           .sort_values(ascending=True))

bars = ax.barh(cat_npa.index, cat_npa.values, color=sns.color_palette("Reds_r", len(cat_npa)))
ax.xaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_xlabel("NPA Ratio (%)")
ax.set_title("Gross NPA Ratio by Product Category", fontsize=14, fontweight="bold")
for bar, val in zip(bars, cat_npa.values):
    ax.text(val + 0.1, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}%", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(OUT / "01_npa_by_product.png")
plt.close()

# ── Chart 2 : DPD Bucket Distribution ────────────────────────────────────────
BUCKET_ORDER = ["Current","1-30","31-60","61-90","91-180","180+"]
dpd_latest = (snaps.sort_values("snapshot_month")
              .groupby("loan_id")
              .last()
              .reset_index())
dpd_dist = dpd_latest["dpd_bucket_current"].value_counts().reindex(BUCKET_ORDER, fill_value=0)

fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#2ecc71","#f1c40f","#e67e22","#e74c3c","#8e44ad","#2c3e50"]
ax.bar(dpd_dist.index, dpd_dist.values, color=colors)
ax.set_xlabel("DPD Bucket")
ax.set_ylabel("Number of Loans")
ax.set_title("Loan Distribution by DPD Bucket", fontsize=14, fontweight="bold")
for i, (idx, val) in enumerate(dpd_dist.items()):
    ax.text(i, val + 200, f"{val:,}", ha="center", fontsize=9)
plt.tight_layout()
plt.savefig(OUT / "02_dpd_distribution.png")
plt.close()

# ── Chart 3 : Monthly Delinquency Trend ───────────────────────────────────────
monthly = (snaps.groupby("snapshot_month")
           .agg(total_balance=("outstanding_balance","sum"),
                npa_balance=("npa_flag", lambda x:
                    (snaps.loc[x.index, "outstanding_balance"] * x).sum()))
           .reset_index())
monthly["npa_ratio"] = monthly["npa_balance"] / monthly["total_balance"] * 100
monthly = monthly.sort_values("snapshot_month").tail(18)

fig, ax1 = plt.subplots(figsize=(12, 5))
ax2 = ax1.twinx()
ax1.fill_between(monthly["snapshot_month"], monthly["total_balance"]/1e6,
                 alpha=0.3, color="#3498db", label="Portfolio (₹M)")
ax1.plot(monthly["snapshot_month"], monthly["total_balance"]/1e6,
         color="#3498db", linewidth=2)
ax2.plot(monthly["snapshot_month"], monthly["npa_ratio"],
         color="#e74c3c", linewidth=2.5, marker="o", ms=4, label="NPA Ratio")
ax1.set_ylabel("Portfolio Balance (₹ Millions)", color="#3498db")
ax2.set_ylabel("NPA Ratio (%)", color="#e74c3c")
ax1.set_xlabel("Month")
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
ax1.set_title("Portfolio Balance & NPA Trend (Last 18 Months)", fontsize=14, fontweight="bold")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1+lines2, labels1+labels2, loc="upper left")
plt.tight_layout()
plt.savefig(OUT / "03_delinquency_trend.png")
plt.close()

# ── Chart 4 : Credit Score Distribution ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
ax.hist(borrowers["credit_score"], bins=50, color="#3498db", edgecolor="white", alpha=0.85)
ax.axvline(620, color="#e74c3c", linestyle="--", linewidth=1.5, label="Sub-prime (<620)")
ax.axvline(700, color="#2ecc71", linestyle="--", linewidth=1.5, label="Prime (≥700)")
ax.set_xlabel("Credit Score")
ax.set_ylabel("Number of Borrowers")
ax.set_title("Borrower Credit Score Distribution", fontsize=14, fontweight="bold")
ax.legend()
plt.tight_layout()
plt.savefig(OUT / "04_credit_score_dist.png")
plt.close()

# ── Chart 5 : Vintage Cohort NPA ─────────────────────────────────────────────
df["cohort_q"] = df["disbursement_date"].dt.to_period("Q").astype(str)
cohort = (df.groupby("cohort_q")
          .apply(lambda x: pd.Series({
              "npa_pct": x.loc[x["npa_flag"]==1,"loan_amount"].sum()
                         / x["loan_amount"].sum() * 100,
              "loans": len(x)
          }))
          .reset_index()
          .sort_values("cohort_q"))

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(cohort["cohort_q"], cohort["npa_pct"],
       color=plt.cm.RdYlGn_r(cohort["npa_pct"] / cohort["npa_pct"].max()))
ax.set_xlabel("Disbursement Quarter")
ax.set_ylabel("NPA % of Cohort")
ax.set_title("Vintage Cohort NPA Rate", fontsize=14, fontweight="bold")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(OUT / "05_vintage_cohort.png")
plt.close()

print(f"\n✓ 5 charts saved to {OUT}/")
print("\nEDA complete.")
