-- ============================================================
-- Credit Portfolio Risk Dashboard
-- Analytical SQL Queries v1.0
-- ============================================================

USE credit_portfolio;

-- ----------------------------------------------------------
-- Q1  NPA Ratio by Product Category
-- ----------------------------------------------------------
SELECT
    lp.product_category,
    COUNT(l.loan_id)                                          AS total_loans,
    SUM(l.outstanding_balance)                               AS total_outstanding,
    SUM(CASE WHEN l.npa_flag = 1 THEN l.outstanding_balance ELSE 0 END)
                                                              AS npa_outstanding,
    ROUND(
        SUM(CASE WHEN l.npa_flag = 1 THEN l.outstanding_balance ELSE 0 END)
        / NULLIF(SUM(l.outstanding_balance), 0) * 100, 2
    )                                                         AS npa_ratio_pct
FROM loans l
JOIN loan_products lp ON l.product_id = lp.product_id
WHERE l.loan_status IN ('Active', 'Restructured')
GROUP BY lp.product_category
ORDER BY npa_ratio_pct DESC;


-- ----------------------------------------------------------
-- Q2  DPD Bucket Distribution (current portfolio)
-- ----------------------------------------------------------
SELECT
    r.dpd_bucket,
    pm.classification,
    pm.provision_pct,
    COUNT(DISTINCT l.loan_id)                                 AS loan_count,
    ROUND(SUM(l.outstanding_balance), 0)                     AS outstanding_balance,
    ROUND(SUM(l.outstanding_balance) * pm.provision_pct / 100, 0)
                                                              AS provision_required
FROM loans l
JOIN (
    SELECT loan_id, dpd_bucket,
           ROW_NUMBER() OVER (PARTITION BY loan_id ORDER BY due_date DESC) AS rn
    FROM repayments
) r ON l.loan_id = r.loan_id AND r.rn = 1
JOIN provision_matrix pm ON r.dpd_bucket = pm.bucket
WHERE l.loan_status = 'Active'
GROUP BY r.dpd_bucket, pm.classification, pm.provision_pct
ORDER BY pm.provision_pct;


-- ----------------------------------------------------------
-- Q3  Monthly Roll-Rate Matrix  (pivot: prior → current bucket)
-- ----------------------------------------------------------
SELECT
    prior_bucket,
    SUM(CASE WHEN current_bucket = 'Current'  THEN cnt ELSE 0 END) AS `Current`,
    SUM(CASE WHEN current_bucket = '1-30'     THEN cnt ELSE 0 END) AS `1_30`,
    SUM(CASE WHEN current_bucket = '31-60'    THEN cnt ELSE 0 END) AS `31_60`,
    SUM(CASE WHEN current_bucket = '61-90'    THEN cnt ELSE 0 END) AS `61_90`,
    SUM(CASE WHEN current_bucket = '91-180'   THEN cnt ELSE 0 END) AS `91_180`,
    SUM(CASE WHEN current_bucket = '180+'     THEN cnt ELSE 0 END) AS `180_plus`
FROM (
    SELECT
        s.dpd_bucket_prior   AS prior_bucket,
        s.dpd_bucket_current AS current_bucket,
        COUNT(*)             AS cnt
    FROM loan_monthly_snapshot s
    WHERE s.snapshot_month = DATE_FORMAT(CURDATE() - INTERVAL 1 MONTH, '%Y-%m-01')
      AND s.dpd_bucket_prior IS NOT NULL
    GROUP BY s.dpd_bucket_prior, s.dpd_bucket_current
) x
GROUP BY prior_bucket;


-- ----------------------------------------------------------
-- Q4  Delinquency Trend – last 12 months
-- ----------------------------------------------------------
SELECT
    DATE_FORMAT(s.snapshot_month, '%Y-%m')                   AS month_year,
    ROUND(SUM(s.outstanding_balance), 0)                     AS total_portfolio,
    ROUND(SUM(CASE WHEN s.npa_flag = 1 THEN s.outstanding_balance ELSE 0 END), 0)
                                                              AS npa_balance,
    ROUND(
        SUM(CASE WHEN s.npa_flag = 1 THEN s.outstanding_balance ELSE 0 END)
        / NULLIF(SUM(s.outstanding_balance), 0) * 100, 2
    )                                                         AS npa_ratio_pct,
    ROUND(SUM(CASE WHEN s.dpd_bucket_current IN ('1-30','31-60','61-90','91-180','180+')
                   THEN s.outstanding_balance ELSE 0 END)
        / NULLIF(SUM(s.outstanding_balance), 0) * 100, 2
    )                                                         AS delinquency_rate_pct
FROM loan_monthly_snapshot s
WHERE s.snapshot_month >= DATE_FORMAT(CURDATE() - INTERVAL 12 MONTH, '%Y-%m-01')
GROUP BY s.snapshot_month
ORDER BY s.snapshot_month;


-- ----------------------------------------------------------
-- Q5  Vintage Cohort Analysis (by disbursement quarter)
-- ----------------------------------------------------------
SELECT
    CONCAT(YEAR(l.disbursement_date), '-Q',
           QUARTER(l.disbursement_date))                     AS cohort_quarter,
    COUNT(l.loan_id)                                          AS loans_disbursed,
    ROUND(SUM(l.loan_amount), 0)                             AS amount_disbursed,
    ROUND(SUM(CASE WHEN l.npa_flag = 1 THEN l.loan_amount ELSE 0 END)
        / NULLIF(SUM(l.loan_amount), 0) * 100, 2
    )                                                         AS cohort_npa_pct,
    ROUND(AVG(b.credit_score), 0)                            AS avg_credit_score,
    ROUND(AVG(l.ltv_ratio), 2)                               AS avg_ltv
FROM loans l
JOIN borrowers b ON l.borrower_id = b.borrower_id
GROUP BY cohort_quarter
ORDER BY cohort_quarter;


-- ----------------------------------------------------------
-- Q6  Regional Heat Map – NPA by State
-- ----------------------------------------------------------
SELECT
    br.state,
    br.region,
    COUNT(l.loan_id)                                          AS total_loans,
    ROUND(SUM(l.outstanding_balance) / 1e6, 2)              AS outstanding_mn,
    ROUND(SUM(CASE WHEN l.npa_flag=1 THEN l.outstanding_balance ELSE 0 END)/1e6,2)
                                                              AS npa_mn,
    ROUND(
        SUM(CASE WHEN l.npa_flag=1 THEN l.outstanding_balance ELSE 0 END)
        / NULLIF(SUM(l.outstanding_balance),0)*100, 2
    )                                                         AS npa_ratio_pct
FROM loans l
JOIN branches br ON l.branch_code = br.branch_code
WHERE l.loan_status IN ('Active','Restructured')
GROUP BY br.state, br.region
ORDER BY npa_ratio_pct DESC;


-- ----------------------------------------------------------
-- Q7  Early Warning Signal – high-risk loans
-- ----------------------------------------------------------
SELECT
    l.loan_id,
    b.borrower_id,
    CONCAT(b.first_name,' ',b.last_name)                     AS borrower_name,
    b.credit_score,
    lp.product_category,
    l.outstanding_balance,
    r.dpd_bucket,
    r.days_past_due,
    l.ltv_ratio,
    -- composite risk score (higher = riskier)
    ROUND(
        (CASE r.dpd_bucket
            WHEN 'Current' THEN 0  WHEN '1-30'  THEN 20
            WHEN '31-60'   THEN 40 WHEN '61-90' THEN 60
            WHEN '91-180'  THEN 80 WHEN '180+'  THEN 100
         END) * 0.5
      + GREATEST(0, (700 - b.credit_score) / 4) * 0.3
      + LEAST(100, COALESCE(l.ltv_ratio,0)) * 0.2
    , 1)                                                      AS risk_score
FROM loans l
JOIN borrowers b     ON l.borrower_id  = b.borrower_id
JOIN loan_products lp ON l.product_id  = lp.product_id
JOIN (
    SELECT loan_id, dpd_bucket, days_past_due,
           ROW_NUMBER() OVER (PARTITION BY loan_id ORDER BY due_date DESC) AS rn
    FROM repayments
) r ON l.loan_id = r.loan_id AND r.rn = 1
WHERE l.loan_status = 'Active'
  AND (r.days_past_due > 0 OR b.credit_score < 620 OR l.ltv_ratio > 80)
ORDER BY risk_score DESC
LIMIT 500;


-- ----------------------------------------------------------
-- Q8  Provision Coverage Ratio
-- ----------------------------------------------------------
SELECT
    ROUND(SUM(CASE WHEN l.npa_flag=1 THEN s.provision_amount ELSE 0 END)
        / NULLIF(SUM(CASE WHEN l.npa_flag=1 THEN l.outstanding_balance ELSE 0 END),0)*100, 2)
        AS provision_coverage_ratio_pct,
    ROUND(SUM(s.provision_amount)/1e6,2)                     AS total_provision_mn,
    ROUND(SUM(CASE WHEN l.npa_flag=1 THEN l.outstanding_balance ELSE 0 END)/1e6,2)
                                                              AS gross_npa_mn
FROM loans l
JOIN (
    SELECT loan_id, provision_amount,
           ROW_NUMBER() OVER (PARTITION BY loan_id ORDER BY snapshot_month DESC) AS rn
    FROM loan_monthly_snapshot
) s ON l.loan_id = s.loan_id AND s.rn = 1;
