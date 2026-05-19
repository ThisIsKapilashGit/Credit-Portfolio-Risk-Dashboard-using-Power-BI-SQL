# Power BI Setup Guide — Credit Portfolio Risk Dashboard

## Prerequisites
- Power BI Desktop (latest)
- MySQL 8.0 or higher
- MySQL ODBC Connector for Windows

---

## Step 1: Load Data into MySQL

```sql
-- Run schema first
source sql/01_schema.sql;

-- Then bulk-load CSVs via mysqlimport (see README)
```

---

## Step 2: Connect Power BI to MySQL

1. Open **Power BI Desktop**
2. Click **Home → Get Data → More → Database → MySQL database**
3. Enter:
   - **Server**: `localhost`
   - **Database**: `credit_portfolio`
4. Choose **Import** mode (recommended for <500 MB)
5. Select all 7 tables → **Load**

---

## Step 3: Build the Data Model

In **Model view**, create these relationships:

| From (Many) | To (One) | Join Column |
|---|---|---|
| loans | borrowers | borrower_id |
| loans | loan_products | product_id |
| loans | branches | branch_code |
| repayments | loans | loan_id |
| loan_monthly_snapshot | loans | loan_id |
| repayments | provision_matrix | dpd_bucket = bucket |

Set all cardinality to **Many-to-One (*)→(1)**, cross-filter **Single**.

---

## Step 4: Add a Date Table

In Power Query (M):

```m
let
    StartDate = #date(2018, 1, 1),
    EndDate   = Date.From(DateTime.LocalNow()),
    DateList  = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1,0,0,0)),
    #"Table"  = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),
    #"Date"   = Table.TransformColumnTypes(#"Table",{{"Date", type date}}),
    #"Year"   = Table.AddColumn(#"Date", "Year", each Date.Year([Date]), Int32.Type),
    #"Month"  = Table.AddColumn(#"Year", "Month", each Date.Month([Date]), Int32.Type),
    #"MonthName" = Table.AddColumn(#"Month", "Month Name", each Date.ToText([Date],"MMM"), type text),
    #"Quarter"   = Table.AddColumn(#"MonthName", "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date])), type text)
in
    #"Quarter"
```

Mark as **Date Table** → relate to `loans[disbursement_date]`.

---

## Step 5: Paste DAX Measures

Open `dax/measures.dax` and paste each block via **Modeling → New Measure**.

Organize into display folders:
- `01_Volume`
- `02_NPA`
- `03_DPD Buckets`
- `04_Provisions`
- `05_Roll Rates`
- `06_Time Intelligence`
- `07_Credit Quality`

---

## Step 6: Build Visuals

### Page 1 — Executive Summary
| Visual | Fields |
|---|---|
| Card | Gross NPA Ratio % |
| Card | Delinquency Rate |
| Card | Provision Coverage Ratio % |
| Card | Active Loans |
| Line chart | X: snapshot_month, Y: Gross NPA Ratio, Rolling 3M Avg NPA Ratio |
| Donut | Legend: product_category, Values: Total Outstanding Balance |
| Slicer | loan_products[product_category] |
| Slicer | Date table[Year] |

### Page 2 — DPD & Roll-Rate
| Visual | Fields |
|---|---|
| Stacked bar | Axis: dpd_bucket (ordered), Values: Balance per bucket measures |
| Matrix | Rows: dpd_bucket_prior, Columns: dpd_bucket_current, Values: Count of loan_id |
| Table | loan_id, borrower_name, outstanding_balance, dpd_bucket, days_past_due, risk_score |

**Conditional formatting** on the matrix: Data bars or color scale (green → red).

### Page 3 — Vintage
| Visual | Fields |
|---|---|
| Clustered bar | Axis: cohort_q, Values: Cohort NPA % |
| Scatter | X: credit_score, Y: Gross NPA Ratio, Size: Total Outstanding Balance |

### Page 4 — Geography
| Visual | Fields |
|---|---|
| Filled map | Location: state, Color saturation: Gross NPA Ratio % |
| Bar chart | Axis: branch_name, Values: Gross NPA Ratio % (top 10 filter) |

---

## Step 7: Schedule Refresh (Power BI Service)

1. Publish to **Power BI Service**
2. **Datasets → Settings → Gateway connection** → add your on-prem gateway
3. Set **Scheduled refresh** to daily at 07:00 AM
4. Enable **Email notifications** on refresh failure

---

## Tips for Performance

- Add **aggregations** on `loan_monthly_snapshot` for large datasets
- Use **DirectQuery** only if real-time data is needed
- Enable **Query reduction** in Report settings to reduce filter interactions
- Set **Row-level security** by `branch_code` for regional managers
