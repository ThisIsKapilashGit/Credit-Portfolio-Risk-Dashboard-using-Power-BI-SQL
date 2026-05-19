-- ============================================================
-- Credit Portfolio Risk Dashboard
-- Database Schema v1.0
-- ============================================================

CREATE DATABASE IF NOT EXISTS credit_portfolio;
USE credit_portfolio;

-- ----------------------------------------------------------
-- 1. BORROWERS
-- ----------------------------------------------------------
CREATE TABLE borrowers (
    borrower_id       VARCHAR(20)    PRIMARY KEY,
    first_name        VARCHAR(50)    NOT NULL,
    last_name         VARCHAR(50)    NOT NULL,
    date_of_birth     DATE           NOT NULL,
    credit_score      SMALLINT       NOT NULL CHECK (credit_score BETWEEN 300 AND 850),
    annual_income     DECIMAL(15,2)  NOT NULL,
    employment_status VARCHAR(30)    NOT NULL,   -- 'Employed','Self-Employed','Unemployed','Retired'
    state             CHAR(2)        NOT NULL,
    city              VARCHAR(60)    NOT NULL,
    customer_since    DATE           NOT NULL,
    created_at        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------
-- 2. LOAN PRODUCTS
-- ----------------------------------------------------------
CREATE TABLE loan_products (
    product_id        VARCHAR(10)    PRIMARY KEY,
    product_name      VARCHAR(60)    NOT NULL,
    product_category  VARCHAR(30)    NOT NULL,   -- 'Home Loan','Auto Loan','Personal Loan','Credit Card','SME Loan'
    min_amount        DECIMAL(15,2)  NOT NULL,
    max_amount        DECIMAL(15,2)  NOT NULL,
    base_rate         DECIMAL(5,2)   NOT NULL,   -- annual base interest rate (%)
    max_tenure_months SMALLINT       NOT NULL,
    created_at        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------
-- 3. LOANS  (fact table)
-- ----------------------------------------------------------
CREATE TABLE loans (
    loan_id            VARCHAR(20)   PRIMARY KEY,
    borrower_id        VARCHAR(20)   NOT NULL REFERENCES borrowers(borrower_id),
    product_id         VARCHAR(10)   NOT NULL REFERENCES loan_products(product_id),
    loan_amount        DECIMAL(15,2) NOT NULL,
    outstanding_balance DECIMAL(15,2) NOT NULL,
    interest_rate      DECIMAL(5,2)  NOT NULL,
    tenure_months      SMALLINT      NOT NULL,
    emi_amount         DECIMAL(12,2) NOT NULL,
    disbursement_date  DATE          NOT NULL,
    maturity_date      DATE          NOT NULL,
    loan_status        VARCHAR(20)   NOT NULL,   -- 'Active','Closed','Written-Off','Restructured'
    npa_flag           TINYINT(1)    NOT NULL DEFAULT 0,  -- 1 = NPA
    npa_since_date     DATE,
    collateral_value   DECIMAL(15,2),
    ltv_ratio          DECIMAL(5,2),             -- loan-to-value %
    branch_code        VARCHAR(10),
    created_at         TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_borrower   (borrower_id),
    INDEX idx_product    (product_id),
    INDEX idx_status     (loan_status),
    INDEX idx_npa        (npa_flag),
    INDEX idx_disburse   (disbursement_date)
);

-- ----------------------------------------------------------
-- 4. REPAYMENTS  (monthly EMI ledger)
-- ----------------------------------------------------------
CREATE TABLE repayments (
    repayment_id      BIGINT        AUTO_INCREMENT PRIMARY KEY,
    loan_id           VARCHAR(20)   NOT NULL REFERENCES loans(loan_id),
    due_date          DATE          NOT NULL,
    paid_date         DATE,
    emi_due           DECIMAL(12,2) NOT NULL,
    principal_due     DECIMAL(12,2) NOT NULL,
    interest_due      DECIMAL(12,2) NOT NULL,
    amount_paid       DECIMAL(12,2) DEFAULT 0,
    days_past_due     SMALLINT      DEFAULT 0,
    payment_status    VARCHAR(20)   NOT NULL,    -- 'Paid','Partially Paid','Unpaid','Waived'
    dpd_bucket        VARCHAR(20)   NOT NULL,    -- 'Current','1-30','31-60','61-90','91-180','180+'
    created_at        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_loan_id  (loan_id),
    INDEX idx_due_date (due_date),
    INDEX idx_dpd      (days_past_due),
    INDEX idx_bucket   (dpd_bucket)
);

-- ----------------------------------------------------------
-- 5. LOAN MONTHLY SNAPSHOT  (for roll-rate / vintage analysis)
-- ----------------------------------------------------------
CREATE TABLE loan_monthly_snapshot (
    snapshot_id          BIGINT       AUTO_INCREMENT PRIMARY KEY,
    snapshot_month       DATE         NOT NULL,           -- first day of month
    loan_id              VARCHAR(20)  NOT NULL,
    dpd_bucket_current   VARCHAR(20)  NOT NULL,
    dpd_bucket_prior     VARCHAR(20),
    outstanding_balance  DECIMAL(15,2),
    npa_flag             TINYINT(1)   DEFAULT 0,
    provision_amount     DECIMAL(15,2),
    INDEX idx_snap_month  (snapshot_month),
    INDEX idx_snap_loan   (loan_id),
    UNIQUE KEY uq_snap    (snapshot_month, loan_id)
);

-- ----------------------------------------------------------
-- 6. BRANCHES
-- ----------------------------------------------------------
CREATE TABLE branches (
    branch_code   VARCHAR(10)  PRIMARY KEY,
    branch_name   VARCHAR(100) NOT NULL,
    region        VARCHAR(30)  NOT NULL,
    state         CHAR(2)      NOT NULL,
    city          VARCHAR(60)  NOT NULL,
    branch_type   VARCHAR(20)  NOT NULL    -- 'Metro','Urban','Semi-Urban','Rural'
);

-- ----------------------------------------------------------
-- 7. PROVISION MATRIX  (regulatory provisioning rates)
-- ----------------------------------------------------------
CREATE TABLE provision_matrix (
    bucket        VARCHAR(20)   PRIMARY KEY,
    provision_pct DECIMAL(5,2)  NOT NULL,
    classification VARCHAR(30)  NOT NULL
);

INSERT INTO provision_matrix VALUES
  ('Current',  0.40,  'Standard'),
  ('1-30',     1.00,  'Special Mention'),
  ('31-60',    5.00,  'Sub-Standard'),
  ('61-90',   15.00,  'Sub-Standard'),
  ('91-180',  25.00,  'Doubtful'),
  ('180+',   100.00,  'Loss');
