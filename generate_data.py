"""
Credit Portfolio Risk Dashboard
Synthetic Data Generator — generates 100,000+ realistic loan records
Usage:  python generate_data.py [--records 100000] [--seed 42]
Output: data/loans.csv, data/borrowers.csv, data/repayments.csv, ...
"""

import argparse
import csv
import math
import os
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np

# ── reproducibility ────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--records", type=int, default=100_000)
parser.add_argument("--seed",    type=int, default=42)
args = parser.parse_args()

random.seed(args.seed)
np.random.seed(args.seed)

OUT = Path("data")
OUT.mkdir(exist_ok=True)

# ── reference data ─────────────────────────────────────────────────────────────
STATES = ["CA","TX","NY","FL","IL","PA","OH","GA","NC","MI",
          "NJ","VA","WA","AZ","MA","TN","IN","MO","MD","WI"]

PRODUCT_CATALOG = [
    ("PL001", "Personal Loan – Salaried",   "Personal Loan",  10_000, 500_000,  11.5,  60),
    ("PL002", "Personal Loan – Self-Emp",   "Personal Loan",  10_000, 300_000,  14.0,  48),
    ("HL001", "Home Loan – Fixed",          "Home Loan",     500_000, 10_000_000, 8.5, 240),
    ("HL002", "Home Loan – Floating",       "Home Loan",     500_000, 10_000_000, 8.0, 240),
    ("AL001", "Auto Loan – New Vehicle",    "Auto Loan",      50_000, 1_500_000,  9.5,  84),
    ("AL002", "Auto Loan – Used Vehicle",   "Auto Loan",      30_000,   800_000, 12.0,  60),
    ("CC001", "Credit Card – Classic",      "Credit Card",     5_000,   200_000, 24.0,  36),
    ("CC002", "Credit Card – Platinum",     "Credit Card",    20_000,   500_000, 18.0,  36),
    ("SM001", "SME Term Loan",              "SME Loan",      200_000, 5_000_000, 13.5, 120),
    ("SM002", "SME Working Capital",        "SME Loan",      100_000, 2_000_000, 15.0,  36),
]

EMPLOYMENT_STATUS = ["Employed", "Self-Employed", "Unemployed", "Retired"]
DPD_BUCKETS       = ["Current", "1-30", "31-60", "61-90", "91-180", "180+"]
BRANCH_TYPES      = ["Metro", "Urban", "Semi-Urban", "Rural"]

# ── helpers ────────────────────────────────────────────────────────────────────
def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def calc_emi(principal: float, annual_rate: float, months: int) -> float:
    r = annual_rate / 12 / 100
    if r == 0:
        return principal / months
    return principal * r * (1 + r)**months / ((1 + r)**months - 1)

def days_to_bucket(dpd: int) -> str:
    if dpd == 0:   return "Current"
    if dpd <= 30:  return "1-30"
    if dpd <= 60:  return "31-60"
    if dpd <= 90:  return "61-90"
    if dpd <= 180: return "91-180"
    return "180+"

def provision_rate(bucket: str) -> float:
    return {"Current":0.004,"1-30":0.01,"31-60":0.05,
            "61-90":0.15,"91-180":0.25,"180+":1.0}.get(bucket, 0)

# ── 1. BRANCHES ────────────────────────────────────────────────────────────────
print("Generating branches …")
branches = []
for i, state in enumerate(STATES):
    for j, btype in enumerate(BRANCH_TYPES):
        branches.append({
            "branch_code": f"BR{i:02d}{j:02d}",
            "branch_name": f"{state} {btype} Branch {j+1}",
            "region": "West" if state in ["CA","WA","AZ"] else
                      "East" if state in ["NY","NJ","MA","PA","MD"] else
                      "South" if state in ["TX","FL","GA","NC","TN"] else "Midwest",
            "state":       state,
            "city":        f"{state}_City_{j+1}",
            "branch_type": btype,
        })

with open(OUT / "branches.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=branches[0].keys())
    w.writeheader(); w.writerows(branches)

branch_codes = [b["branch_code"] for b in branches]

# ── 2. LOAN PRODUCTS ───────────────────────────────────────────────────────────
print("Generating loan products …")
with open(OUT / "loan_products.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["product_id","product_name","product_category",
                     "min_amount","max_amount","base_rate","max_tenure_months"])
    writer.writerows(PRODUCT_CATALOG)

# ── 3. BORROWERS ───────────────────────────────────────────────────────────────
N = args.records
print(f"Generating {N:,} borrowers …")

FIRST = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda",
         "David","Barbara","William","Elizabeth","Richard","Susan","Joseph","Sarah"]
LAST  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
         "Wilson","Taylor","Anderson","Thomas","Jackson","White","Harris","Martin"]

borrowers = []
for i in range(N):
    cs = int(np.clip(np.random.normal(670, 80), 300, 850))
    emp = random.choices(EMPLOYMENT_STATUS, weights=[55,25,10,10])[0]
    income = np.clip(np.random.lognormal(11.0, 0.6), 20_000, 2_000_000)
    dob = rand_date(date(1950,1,1), date(2000,12,31))
    borrowers.append({
        "borrower_id":     f"B{i+1:07d}",
        "first_name":      random.choice(FIRST),
        "last_name":       random.choice(LAST),
        "date_of_birth":   dob,
        "credit_score":    cs,
        "annual_income":   round(income, 2),
        "employment_status": emp,
        "state":           random.choice(STATES),
        "city":            f"City_{random.randint(1,50)}",
        "customer_since":  rand_date(date(2010,1,1), date(2023,6,30)),
    })

with open(OUT / "borrowers.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=borrowers[0].keys())
    w.writeheader(); w.writerows(borrowers)

print(f"  ✓ {len(borrowers):,} borrowers written")

# ── 4. LOANS ───────────────────────────────────────────────────────────────────
print("Generating loans …")

products = {p[0]: p for p in PRODUCT_CATALOG}

def pick_product(credit_score: int) -> tuple:
    weights = []
    for p in PRODUCT_CATALOG:
        if credit_score >= 700:
            w = 3 if p[0].startswith("HL") else \
                2 if p[0].startswith("AL") else 1
        elif credit_score >= 600:
            w = 2 if p[0].startswith("PL") else \
                1 if p[0].startswith("AL") else 1
        else:
            w = 3 if p[0].startswith("CC") else \
                2 if p[0].startswith("PL") else 0.5
        weights.append(w)
    return random.choices(PRODUCT_CATALOG, weights=weights)[0]

loans, loan_rows = [], []
today = date.today()
for i, b in enumerate(borrowers):
    prod = pick_product(b["credit_score"])
    pid, _, cat, mn, mx, rate, max_ten = prod

    # loan amount — correlated with income
    amount = np.clip(
        np.random.lognormal(math.log(min(b["annual_income"]*2, mx)), 0.4),
        mn, mx
    )
    amount = round(amount / 1000) * 1000

    tenure = random.choice([12,24,36,48,60,84,120,180,240])
    tenure = min(tenure, max_ten)

    # bump rate slightly for riskier borrowers
    r_adj  = rate + max(0, (650 - b["credit_score"]) * 0.02)
    r_adj  = round(r_adj, 2)

    disb = rand_date(date(2018,1,1), date(2024,6,30))
    maty = disb + timedelta(days=tenure * 30)

    emi = round(calc_emi(amount, r_adj, tenure), 2)

    # months elapsed since disbursement
    months_elapsed = (today - disb).days // 30
    months_elapsed = max(0, min(months_elapsed, tenure))

    # outstanding balance (simplified amortisation)
    remaining = tenure - months_elapsed
    if remaining <= 0:
        outstanding = 0.0
        status = "Closed"
    else:
        r = r_adj / 12 / 100
        outstanding = round(
            amount * (1+r)**months_elapsed
            - emi * ((1+r)**months_elapsed - 1) / r
        , 2) if r > 0 else round(amount - emi * months_elapsed, 2)
        outstanding = max(0, outstanding)
        status = "Active"

    # NPA logic — bad credit or high LTV → higher probability
    ltv = round(random.uniform(40, 95), 2) if cat in ("Home Loan","Auto Loan") else None
    npa_prob = 0.03
    if b["credit_score"] < 580: npa_prob += 0.12
    elif b["credit_score"] < 640: npa_prob += 0.06
    if ltv and ltv > 85: npa_prob += 0.04
    if b["employment_status"] == "Unemployed": npa_prob += 0.05

    npa = 1 if (random.random() < npa_prob and status == "Active") else 0
    npa_date = rand_date(disb + timedelta(days=90), today) if npa else None

    if npa: status = "Active"  # NPA loans stay active until written off

    wr_prob = 0.005
    if random.random() < wr_prob and status == "Active":
        status = "Written-Off"; npa = 1

    loans.append({
        "loan_id":            f"L{i+1:08d}",
        "borrower_id":        b["borrower_id"],
        "product_id":         pid,
        "loan_amount":        amount,
        "outstanding_balance": outstanding if status != "Closed" else 0,
        "interest_rate":      r_adj,
        "tenure_months":      tenure,
        "emi_amount":         emi,
        "disbursement_date":  disb,
        "maturity_date":      maty,
        "loan_status":        status,
        "npa_flag":           npa,
        "npa_since_date":     npa_date,
        "collateral_value":   round(amount / (ltv/100), 2) if ltv else None,
        "ltv_ratio":          ltv,
        "branch_code":        random.choice(branch_codes),
    })

with open(OUT / "loans.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=loans[0].keys())
    w.writeheader(); w.writerows(loans)

print(f"  ✓ {len(loans):,} loans written")

# ── 5. REPAYMENTS ──────────────────────────────────────────────────────────────
print("Generating repayments (this may take ~60 s for 100 K loans) …")

REPAY_FILE = OUT / "repayments.csv"
SNAP_FILE  = OUT / "loan_monthly_snapshot.csv"

rep_fields  = ["repayment_id","loan_id","due_date","paid_date","emi_due",
               "principal_due","interest_due","amount_paid","days_past_due",
               "payment_status","dpd_bucket"]
snap_fields = ["snapshot_id","snapshot_month","loan_id","dpd_bucket_current",
               "dpd_bucket_prior","outstanding_balance","npa_flag","provision_amount"]

rep_id = 1; snap_id = 1
written_reps = 0; written_snaps = 0

with open(REPAY_FILE, "w", newline="") as fr, \
     open(SNAP_FILE,  "w", newline="") as fs:

    rw = csv.DictWriter(fr, fieldnames=rep_fields)
    sw = csv.DictWriter(fs, fieldnames=snap_fields)
    rw.writeheader(); sw.writeheader()

    loan_map = {l["loan_id"]: l for l in loans}

    for idx, loan in enumerate(loans):
        if idx % 10_000 == 0:
            print(f"    {idx:,} / {len(loans):,} loans processed …")

        if loan["loan_status"] == "Closed":
            continue

        disb   = loan["disbursement_date"]
        tenure = loan["tenure_months"]
        emi    = loan["emi_amount"]
        rate   = loan["interest_rate"] / 12 / 100
        bal    = loan["loan_amount"]
        npa    = loan["npa_flag"]

        # delinquency profile
        if npa:
            dpd_onset = random.randint(3, tenure - 1)
        else:
            dpd_onset = None

        prev_bucket = None

        for m in range(1, min(tenure + 1, 85)):   # cap at 84 months output
            due = disb + timedelta(days=m * 30)
            if due > today:
                break

            # principal / interest split
            interest_due = round(bal * rate, 2)
            principal_due = round(emi - interest_due, 2)
            principal_due = max(0, min(principal_due, bal))

            # days past due logic
            if dpd_onset and m >= dpd_onset:
                dpd = (m - dpd_onset + 1) * 30
                # some cures
                if random.random() < 0.15:
                    dpd = 0
            else:
                dpd = max(0, int(np.random.exponential(2)) * random.choices([0,1],[0.85,0.15])[0])

            bucket = days_to_bucket(dpd)
            if dpd == 0:
                paid    = emi
                pd_date = due + timedelta(days=random.randint(0, 3))
                pstatus = "Paid"
            elif dpd < 30:
                paid    = round(emi * random.uniform(0.5, 0.99), 2)
                pd_date = due + timedelta(days=dpd)
                pstatus = "Partially Paid"
            else:
                paid    = 0.0
                pd_date = None
                pstatus = "Unpaid"

            rw.writerow({
                "repayment_id":  rep_id,
                "loan_id":       loan["loan_id"],
                "due_date":      due,
                "paid_date":     pd_date,
                "emi_due":       emi,
                "principal_due": principal_due,
                "interest_due":  interest_due,
                "amount_paid":   paid,
                "days_past_due": dpd,
                "payment_status": pstatus,
                "dpd_bucket":    bucket,
            })
            rep_id += 1; written_reps += 1

            # snapshot (monthly)
            snap_month = date(due.year, due.month, 1)
            prov = round(loan["outstanding_balance"] * provision_rate(bucket), 2)
            sw.writerow({
                "snapshot_id":         snap_id,
                "snapshot_month":      snap_month,
                "loan_id":             loan["loan_id"],
                "dpd_bucket_current":  bucket,
                "dpd_bucket_prior":    prev_bucket,
                "outstanding_balance": round(bal, 2),
                "npa_flag":            1 if bucket in ("91-180","180+") else 0,
                "provision_amount":    prov,
            })
            snap_id += 1; written_snaps += 1
            prev_bucket = bucket
            bal = max(0, bal - principal_due)

print(f"  ✓ {written_reps:,} repayment rows written")
print(f"  ✓ {written_snaps:,} snapshot rows written")
print("\n🎉 Data generation complete. Files in ./data/")
