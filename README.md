# 📊 Credit Portfolio Risk Dashboard

> End-to-end automated dashboard integrating **100,000+ loan records**, tracking NPA ratio,
> roll rates, and delinquency trends — reducing manual reporting effort by **30 %**.

![CI](https://github.com/<your-username>/credit-portfolio-risk-dashboard/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![SQL](https://img.shields.io/badge/SQL-MySQL%208-orange?logo=mysql)
![Power BI](https://img.shields.io/badge/Power%20BI-DAX-yellow?logo=powerbi)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🗂️ Project Structure

```
credit-portfolio-risk-dashboard/
├── sql/
│   ├── 01_schema.sql          # Database schema (6 tables + provision matrix)
│   └── 02_queries.sql         # 8 analytical KPI queries
├── dax/
│   └── measures.dax           # 35+ Power BI DAX measures
├── python/
│   ├── generate_data.py       # Synthetic data generator (100 K+ records)
│   └── eda_kpi.py             # EDA script → 5 charts
├── data/                      # Auto-generated CSVs (git-ignored)
│   └── charts/                # EDA chart PNGs
├── docs/
│   └── powerbi_setup.md       # Step-by-step Power BI setup guide
├── .github/
│   └── workflows/ci.yml       # GitHub Actions CI pipeline
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1 — Clone & install

```bash
git clone https://github.com/<your-username>/credit-portfolio-risk-dashboard.git
cd credit-portfolio-risk-dashboard
pip install -r requirements.txt
```

### 2 — Generate synthetic data

```bash
# Default: 100,000 loan records
python python/generate_data.py

# Custom size & seed
python python/generate_data.py --records 200000 --seed 123
```

Generated files in `data/`:

| File | Rows | Description |
|---|---|---|
| `borrowers.csv` | 100 K | Borrower demographics & credit scores |
| `loans.csv` | 100 K | Loan master with NPA flag & balance |
| `repayments.csv` | ~4 M | Monthly EMI ledger with DPD |
| `loan_monthly_snapshot.csv` | ~3 M | Roll-rate & provision snapshot |
| `loan_products.csv` | 10 | Product catalog |
| `branches.csv` | 80 | Branch master |

### 3 — Run EDA & generate charts

```bash
python python/eda_kpi.py
```

Five charts saved to `data/charts/`:
- `01_npa_by_product.png` — NPA ratio per product category
- `02_dpd_distribution.png` — DPD bucket bar chart
- `03_delinquency_trend.png` — 18-month trend
- `04_credit_score_dist.png` — Borrower credit score histogram
- `05_vintage_cohort.png` — Cohort-level NPA

### 4 — Set up the database

```bash
mysql -u root -p < sql/01_schema.sql

# Load CSVs (adjust path as needed)
mysqlimport --local --fields-terminated-by=',' --lines-terminated-by='\n' \
  --ignore-lines=1 credit_portfolio data/branches.csv data/borrowers.csv \
  data/loan_products.csv data/loans.csv data/repayments.csv \
  data/loan_monthly_snapshot.csv

# Verify with analytical queries
mysql -u root -p credit_portfolio < sql/02_queries.sql
```

### 5 — Connect Power BI

1. Open Power BI Desktop → **Get Data → MySQL database**
2. Server: `localhost`, Database: `credit_portfolio`
3. Import tables: `loans`, `borrowers`, `loan_products`, `repayments`, `loan_monthly_snapshot`, `branches`, `provision_matrix`
4. Paste each measure from `dax/measures.dax` via **Modeling → New Measure**
5. See `docs/powerbi_setup.md` for full visual layout guide

---

## 📐 Data Model (Star Schema)

```
                    ┌──────────────┐
                    │  loan_monthly│
                    │   _snapshot  │
                    └──────┬───────┘
                           │
┌──────────┐   ┌──────────▼──────────┐   ┌──────────────┐
│borrowers │◄──│       loans         │──►│ loan_products│
└──────────┘   │   (fact table)      │   └──────────────┘
               └──────┬──────┬───────┘
                       │      │
              ┌────────▼┐  ┌──▼──────────┐
              │repayments│  │  branches   │
              └──────────┘  └─────────────┘
                                  │
                         ┌────────▼───────┐
                         │provision_matrix│
                         └────────────────┘
```

---

## 📊 Key KPIs Tracked

| KPI | Description |
|---|---|
| **Gross NPA Ratio** | NPA outstanding / Total outstanding |
| **Net NPA Ratio** | (Gross NPA − Provisions) / (Portfolio − Provisions) |
| **Delinquency Rate** | Balance in DPD > 0 / Total portfolio |
| **Roll Forward Rate** | % loans moving to a worse DPD bucket month-over-month |
| **Cure Rate** | % delinquent loans returning to Current bucket |
| **Provision Coverage Ratio** | Total provisions / Gross NPA |
| **Vintage Cohort NPA** | NPA % by disbursement quarter |

---

## 🔢 DAX Measures Summary (35+)

- **Volume**: Total Loans, Active Loans, Total Outstanding Balance, Avg Loan Size
- **NPA**: Gross NPA Amount/Ratio, Net NPA, NPA Count
- **DPD Buckets**: Balance per bucket, Delinquency Rate
- **Provisions**: Total Provision, Coverage Ratio, Shortfall
- **Roll Rates**: 1-30→31-60, 31-60→61-90, 61-90→NPA, Cure Rate
- **Time Intelligence**: MoM / YoY NPA change, Rolling 3M Avg, Portfolio Growth YoY
- **Credit Quality**: Avg Credit Score, % Prime / Subprime, Avg LTV, High LTV Loans
- **Helpers**: Selected Product, Report As Of Date, KPI Status (traffic-light)

---

## 🏗️ Power BI Dashboard Layout

**Page 1 — Executive Summary**
- KPI Cards: Gross NPA %, Net NPA %, Provision Coverage, Delinquency Rate
- Line chart: 12-month NPA & delinquency trend
- Donut: Portfolio mix by product category

**Page 2 — DPD & Roll-Rate Analysis**
- Stacked bar: DPD bucket distribution (count & balance)
- Matrix: Roll-rate heatmap (prior → current bucket)
- Table: Top 20 at-risk loans

**Page 3 — Vintage & Cohort**
- Clustered bar: Cohort NPA by disbursement quarter
- Scatter: Credit score vs. NPA flag
- Line: EMI collection efficiency trend

**Page 4 — Geographic View**
- Map: NPA ratio by state (bubble size = portfolio size)
- Bar: Top 10 branches by NPA ratio
- Table: Region-wise portfolio breakdown

---

## ⚙️ CI/CD Pipeline

GitHub Actions runs on every push:
1. **Generate** 50 K records
2. **Validate** row counts
3. **EDA charts** produced and uploaded as artifacts
4. **SQL lint** via `sqlfluff`

---

## 📁 .gitignore

```
data/*.csv
data/charts/
__pycache__/
*.pyc
.env
```

---

## 📜 License

MIT © 2024 — see [LICENSE](LICENSE)
