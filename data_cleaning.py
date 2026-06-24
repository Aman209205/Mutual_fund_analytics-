import os
import pandas as pd
import numpy as np

# Ensure the processed directory exists
os.makedirs('data/processed', exist_ok=True)

print("Starting Day 2: Data Cleaning Pipeline...")

# ==========================================
# 1. CLEANING 02_nav_history.csv
# ==========================================
if os.path.exists('data/raw/02_nav_history.csv'):
    print("Processing: 02_nav_history.csv...")
    df_nav = pd.read_csv('data/raw/02_nav_history.csv')
    
    # Standardize column names to lower case to avoid key errors
    df_nav.columns = df_nav.columns.str.strip().str.lower()
    
    # Parse dates to datetime
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    
    # Sort by amfi_code and date, then remove duplicates
    df_nav = df_nav.sort_values(by=['amfi_code', 'date']).drop_duplicates()
    
    # Forward-fill missing NAV for holidays/weekends per fund group
    df_nav['nav'] = df_nav.groupby('amfi_code')['nav'].ffill()
    
    # Validate NAV > 0
    df_nav = df_nav[df_nav['nav'] > 0]
    
    # Save cleaned data
    df_nav.to_csv('data/processed/cleaned_nav_history.csv', index=False)
    print("Success: 02_nav_history.csv cleaned successfully.")
else:
    print("Error: data/raw/02_nav_history.csv not found.")

# ==========================================
# 2. CLEANING 08_investor_transactions.csv
# ==========================================
if os.path.exists('data/raw/08_investor_transactions.csv'):
    print("Processing: 08_investor_transactions.csv...")
    df_tx = pd.read_csv('data/raw/08_investor_transactions.csv')
    
    # Standardize column names to lower case to eliminate spaces/case differences
    df_tx.columns = df_tx.columns.str.strip().str.lower()
    
    # Standardize transaction types if the column exists
    if 'transaction_type' in df_tx.columns:
        tx_mapping = {
            'sip': 'SIP', 'SIP': 'SIP',
            'lumpsum': 'Lumpsum', 'Lump sum': 'Lumpsum', 'Lumpsum': 'Lumpsum',
            'redemption': 'Redemption', 'Redeem': 'Redemption', 'Redemption': 'Redemption'
        }
        df_tx['transaction_type'] = df_tx['transaction_type'].map(tx_mapping).fillna('Lumpsum')
    
    # Look for amount column flexibly
    amount_col = [col for col in df_tx.columns if 'amount' in col]
    if amount_col:
        target_amount = amount_col[0]
        df_tx[target_amount] = pd.to_numeric(df_tx[target_amount], errors='coerce')
        df_tx = df_tx[df_tx[target_amount] > 0]
    else:
        print(f"Warning: Could not find an amount column. Available columns: {list(df_tx.columns)}")
    
    # Fix date formats
    date_col = [col for col in df_tx.columns if 'date' in col]
    if date_col:
        df_tx[date_col[0]] = pd.to_datetime(df_tx[date_col[0]])
    
    # Check KYC status enum values
    if 'kyc_status' in df_tx.columns:
        df_tx['kyc_status'] = df_tx['kyc_status'].str.upper().fillna('PENDING')
    
    df_tx.to_csv('data/processed/cleaned_investor_transactions.csv', index=False)
    print("Success: 08_investor_transactions.csv cleaned successfully.")
else:
    print("Error: data/raw/08_investor_transactions.csv not found.")

# ==========================================
# 3. CLEANING 07_scheme_performance.csv
# ==========================================
if os.path.exists('data/raw/07_scheme_performance.csv'):
    print("Processing: 07_scheme_performance.csv...")
    df_perf = pd.read_csv('data/raw/07_scheme_performance.csv')
    
    # Standardize column names to lower case
    df_perf.columns = df_perf.columns.str.strip().str.lower()
    
    # Validate all return values are numeric
    return_cols = [col for col in df_perf.columns if 'return' in col]
    for col in return_cols:
        df_perf[col] = pd.to_numeric(df_perf[col], errors='coerce').fillna(0.0)
        
    # Check expense_ratio range (0.1% - 2.5%) and flag anomalies
    if 'expense_ratio' in df_perf.columns:
        df_perf['expense_ratio'] = pd.to_numeric(df_perf['expense_ratio'], errors='coerce')
        df_perf['expense_ratio_anomaly'] = np.where(
            (df_perf['expense_ratio'] < 0.1) | (df_perf['expense_ratio'] > 2.5), 1, 0
        )
    
    df_perf.to_csv('data/processed/cleaned_scheme_performance.csv', index=False)
    print("Success: 07_scheme_performance.csv cleaned successfully.")
else:
    print("Error: data/raw/07_scheme_performance.csv not found.")

print("All raw datasets successfully processed and exported to data/processed/")