import sqlite3
import pandas as pd
import numpy as np

db_path = 'bluestock_mf.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Starting Star Schema Warehouse Migration via Safe Pandas Mapping...")

# 1. Safely drop older structures if they exist to prevent overlapping locks
tables_to_drop = [
    'fact_nav_relational', 'fact_transactions_relational', 'fact_performance_relational',
    'dim_fund', 'dim_date'
]
for table in tables_to_drop:
    cursor.execute(f"DROP TABLE IF EXISTS {table};")

# 2. Read structural staging tables into dataframes safely before dropping them
df_nav_stage = pd.read_sql_query("SELECT * FROM fact_nav", conn) if 'fact_nav' in [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")] else pd.DataFrame()
df_tx_stage = pd.read_sql_query("SELECT * FROM fact_transactions", conn) if 'fact_transactions' in [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")] else pd.DataFrame()
df_perf_stage = pd.read_sql_query("SELECT * FROM fact_performance", conn) if 'fact_performance' in [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")] else pd.DataFrame()

# Clean up raw text staging tables immediately to free memory paths
cursor.execute("DROP TABLE IF EXISTS fact_nav;")
cursor.execute("DROP TABLE IF EXISTS fact_transactions;")
cursor.execute("DROP TABLE IF EXISTS fact_performance;")
conn.commit()

# Ensure we have data to extract from
all_amfi = []
if not df_nav_stage.empty: all_amfi.extend(df_nav_stage['amfi_code'].unique())
if not df_tx_stage.empty: all_amfi.extend(df_tx_stage['amfi_code'].unique())
if not df_perf_stage.empty: all_amfi.extend(df_perf_stage['amfi_code'].unique())

# 3. Populate dim_fund dataframe safely
df_fund = pd.DataFrame({'amfi_code': list(set(all_amfi))})
df_fund.insert(0, 'fund_id', range(1, len(df_fund) + 1))
df_fund['scheme_name'] = None
df_fund['fund_house'] = None
df_fund['category'] = None
df_fund['plan'] = None

# 4. Populate dim_date dataframe safely
all_dates = []
if not df_nav_stage.empty and 'date' in df_nav_stage.columns:
    all_dates.extend(df_nav_stage['date'].dropna().unique())
if not df_tx_stage.empty:
    date_cols = [col for col in df_tx_stage.columns if 'date' in col]
    if date_cols:
        all_dates.extend(df_tx_stage[date_cols[0]].dropna().unique())

unique_dates = sorted(list(set(all_dates)))
df_date = pd.DataFrame({'full_date': unique_dates})
df_date.insert(0, 'date_id', range(1, len(df_date) + 1))

# Convert columns systematically using explicit datetime components
dt_series = pd.to_datetime(df_date['full_date'])
df_date['day'] = dt_series.dt.day
df_date['month'] = dt_series.dt.month
df_date['quarter'] = dt_series.dt.quarter
df_date['year'] = dt_series.dt.year

# 5. Map Fact Records safely utilizing vectorized dataframe lookups
print("Mapping relational fields using Pandas keys...")

# Map fact_nav
df_nav_rel = pd.DataFrame()
if not df_nav_stage.empty:
    df_nav_rel = df_nav_stage.merge(df_fund[['fund_id', 'amfi_code']], on='amfi_code', how='inner')
    df_nav_rel = df_nav_rel.merge(df_date[['date_id', 'full_date']], left_on='date', right_on='full_date', how='inner')
    df_nav_rel = df_nav_rel[['fund_id', 'date_id', 'nav']]
    df_nav_rel.insert(0, 'nav_id', range(1, len(df_nav_rel) + 1))

# Map fact_transactions
df_tx_rel = pd.DataFrame()
if not df_tx_stage.empty:
    amount_col = [col for col in df_tx_stage.columns if 'amount' in col][0]
    tx_type_col = [col for col in df_tx_stage.columns if 'type' in col or 'mechanism' in col]
    tx_type = tx_type_col[0] if tx_type_col else 'transaction_type'
    tx_date_col = [col for col in df_tx_stage.columns if 'date' in col][0]
    kyc_col = [col for col in df_tx_stage.columns if 'kyc' in col][0] if any('kyc' in c for c in df_tx_stage.columns) else None

    df_tx_rel = df_tx_stage.merge(df_fund[['fund_id', 'amfi_code']], on='amfi_code', how='inner')
    df_tx_rel = df_tx_rel.merge(df_date[['date_id', 'full_date']], left_on=tx_date_col, right_on='full_date', how='inner')
    
    df_tx_rel['amount_inr'] = df_tx_rel[amount_col]
    df_tx_rel['transaction_type'] = df_tx_rel[tx_type] if tx_type in df_tx_rel.columns else 'Lumpsum'
    df_tx_rel['kyc_status'] = df_tx_rel[kyc_col] if kyc_col else 'PENDING'
    
    df_tx_rel = df_tx_rel[['fund_id', 'date_id', 'transaction_type', 'amount_inr', 'kyc_status']]
    df_tx_rel.insert(0, 'transaction_id', range(1, len(df_tx_rel) + 1))

# Map fact_performance safely with fallback mechanisms
df_perf_rel = pd.DataFrame()
if not df_perf_stage.empty:
    r1 = [c for c in df_perf_stage.columns if '1y' in c or '1_yr' in c or '1yr' in c][0]
    r3 = [c for c in df_perf_stage.columns if '3y' in c or '3_yr' in c or '3yr' in c][0]
    r5 = [c for c in df_perf_stage.columns if '5y' in c or '5_yr' in c or '5yr' in c][0]
    exp = [c for c in df_perf_stage.columns if 'expense' in c][0]
    
    # Check if anomaly column exists, otherwise calculate on the fly
    anom_cols = [c for c in df_perf_stage.columns if 'anomaly' in c]
    
    df_perf_rel = df_perf_stage.merge(df_fund[['fund_id', 'amfi_code']], on='amfi_code', how='inner')
    df_perf_rel['return_1yr_pct'] = df_perf_rel[r1]
    df_perf_rel['return_3yr_pct'] = df_perf_rel[r3]
    df_perf_rel['return_5yr_pct'] = df_perf_rel[r5]
    df_perf_rel['expense_ratio_pct'] = df_perf_rel[exp]
    
    if anom_cols:
        df_perf_rel['expense_ratio_anomaly'] = df_perf_rel[anom_cols[0]]
    else:
        # Calculate anomaly if it's missing (outside 0.1% - 2.5% range)
        df_perf_rel['expense_ratio_anomaly'] = np.where(
            (df_perf_rel['expense_ratio_pct'] < 0.1) | (df_perf_rel['expense_ratio_pct'] > 2.5), 1, 0
        )
    
    df_perf_rel = df_perf_rel[['fund_id', 'return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'expense_ratio_pct', 'expense_ratio_anomaly']]
    df_perf_rel.insert(0, 'performance_id', range(1, len(df_perf_rel) + 1))

# 6. Push fully mapped dataframes back into SQLite database warehouse structures
print("Writing relational analytical configurations to SQLite tables...")
df_fund.to_sql('dim_fund', con=conn, if_exists='replace', index=False)
df_date.to_sql('dim_date', con=conn, if_exists='replace', index=False)

if not df_nav_rel.empty: df_nav_rel.to_sql('fact_nav_relational', con=conn, if_exists='replace', index=False)
if not df_tx_rel.empty: df_tx_rel.to_sql('fact_transactions_relational', con=conn, if_exists='replace', index=False)
if not df_perf_rel.empty: df_perf_rel.to_sql('fact_performance_relational', con=conn, if_exists='replace', index=False)

conn.close()
print("Success! Star schema architecture fully built and loaded.")