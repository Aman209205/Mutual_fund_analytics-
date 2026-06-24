import os
import pandas as pd
from sqlalchemy import create_engine

# Path to the SQLite database
db_path = 'bluestock_mf.db'
engine = create_engine(f'sqlite:///{db_path}')

print("Starting Database Loader Pipeline...")

# Mapping processed files to their targeted star schema table structures
datasets = {
    'data/processed/cleaned_nav_history.csv': 'fact_nav',
    'data/processed/cleaned_investor_transactions.csv': 'fact_transactions',
    'data/processed/cleaned_scheme_performance.csv': 'fact_performance'
}

for file_path, table_name in datasets.items():
    if os.path.exists(file_path):
        print(f"Loading {file_path} into SQL table '{table_name}'...")
        
        # Read the processed clean dataset
        df = pd.read_csv(file_path)
        
        # Write dataset to SQLite (overwrites existing table structure securely)
        df.to_sql(table_name, con=engine, if_exists='replace', index=False)
        
        # Integrity verification
        csv_count = len(df)
        db_count = pd.read_sql_query(f"SELECT COUNT(*) FROM {table_name}", engine).iloc[0, 0]
        
        if csv_count == db_count:
            print(f"Success: Row counts match seamlessly ({csv_count} rows loaded).")
        else:
            print(f"Warning: Discrepancy spotted! CSV count: {csv_count}, Database count: {db_count}")
    else:
        print(f"Error: Processed file path not found: {file_path}")

print("\nDatabase processing complete! 'bluestock_mf.db' is ready for analytical use.")