# Data Dictionary - Mutual Fund Analytics Data Warehouse

This document provides a comprehensive overview of the tables, column types, and data definitions for the cleaned datasets loaded into the `bluestock_mf.db` SQLite database.

---

## 1. Table: `fact_nav`
**Source:** `cleaned_nav_history.csv`  
**Description:** Contains historical Net Asset Value (NAV) records for various mutual fund schemes, with missing values forward-filled for holidays and weekends.

| Column Name | Data Type | Description | Key Type |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | Unique identification number for the mutual fund scheme. | Foreign Key |
| `date` | TEXT/DATETIME | The transactional or market valuation date. | Composite Key |
| `nav` | REAL | Net Asset Value of the scheme on that specific day (Validated > 0). | None |

---

## 2. Table: `fact_transactions`
**Source:** `cleaned_investor_transactions.csv`  
**Description:** Tracks investor-level transactions including subscriptions, systematic investments, and redemptions.

| Column Name | Data Type | Description | Key Type |
| :--- | :--- | :--- | :--- |
| `transaction_id` | TEXT/INTEGER | Unique tracking identifier for each transaction sequence. | Primary Key |
| `amfi_code` | INTEGER | Scheme identification code matching the asset identity. | Foreign Key |
| `transaction_date`| TEXT/DATETIME | The exact date when the transaction was executed. | None |
| `transaction_type`| TEXT | Standardized transaction mechanism: `SIP`, `Lumpsum`, or `Redemption`. | None |
| `amount` | REAL | The total monetary value of the transaction (Validated > 0). | None |
| `kyc_status` | TEXT | Investor compliance profiling state: `APPROVED`, `REJECTED`, or `PENDING`. | None |

---

## 3. Table: `fact_performance`
**Source:** `cleaned_scheme_performance.csv`  
**Description:** Aggregated historical metrics evaluating scheme return velocity alongside integrated expense overhead analysis.

| Column Name | Data Type | Description | Key Type |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | Scheme identifier linking back to primary assets. | Primary/Foreign Key |
| `return_1y` | REAL | Standardized 1-Year historical trailing return profile (%). | None |
| `return_3y` | REAL | Standardized 3-Year historical trailing return profile (%). | None |
| `return_5y` | REAL | Standardized 5-Year historical trailing return profile (%). | None |
| `expense_ratio` | REAL | Total annual fund operating expenses expressed as a percentage. | None |
| `expense_ratio_anomaly`| INTEGER | Binary flag marking out-of-bounds expense rates: `1` if outside (0.1% - 2.5%), `0` otherwise. | None |