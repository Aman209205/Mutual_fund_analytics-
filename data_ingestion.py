import pandas as pd
import os
import glob

def check_file_quality(file_path):
    print(f"\n{'='*50}")
    print(f"Exploring: {os.path.basename(file_path)}")
    print(f"{'='*50}")
    
    df = pd.read_csv(file_path)
    print(f"• Shape (Rows, Columns): {df.shape}")
    print("\n• Data Types:")
    print(df.dtypes)
    print("\n• First 2 Rows:")
    print(df.head(2))
    
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print("\n Anomalies / Missing Values found:")
        print(missing[missing > 0])
    else:
        print("\n No missing values detected.")
        
    return df

def main():
    # FIX: Script ki directory automatic dhoondhne ke liye path handling
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(script_dir, "data", "raw")
    
    csv_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    provided_files = [f for f in csv_files if "live_nav_history" not in f]
    
    print(f"Found {len(provided_files)} provided CSV datasets in {raw_dir}.\n")
    
    dfs = {}
    for file in provided_files:
        filename = os.path.basename(file).lower()
        df = check_file_quality(file)
        dfs[filename] = df

    # Target specific validation files from folder structure
    master_key = next((k for k in dfs.keys() if "fund_master" in k), None)
    history_key = next((k for k in dfs.keys() if "nav_history" in k and "live" not in k), None)
    
    if master_key and history_key:
        fund_master = dfs[master_key]
        nav_history = dfs[history_key]
        
        print(f"\n{'='*50}")
        print("RUNNING ADVANCED DATA VALIDATION")
        print(f"{'='*50}")
        
        fund_house_col = next((c for c in fund_master.columns if 'fund' in c.lower()), None)
        scheme_code_col = next((c for c in fund_master.columns if 'code' in c.lower() or 'amfi' in c.lower()), None)
        history_code_col = next((c for c in nav_history.columns if 'code' in c.lower() or 'amfi' in c.lower()), None)
        
        if fund_house_col:
            print(f"• Unique Fund Houses: {fund_master[fund_house_col].nunique()}")
        
        if scheme_code_col and history_code_col:
            master_codes = set(fund_master[scheme_code_col].unique())
            history_codes = set(nav_history[history_code_col].unique())
            missing_in_history = master_codes - history_codes
            
            print("\n Data Quality Summary:")
            if not missing_in_history:
                print("  Pass: Every single AMFI code in fund_master exists in nav_history.")
            else:
                print(f"  Warning: {len(missing_in_history)} codes from fund_master are missing in nav_history.")
    else:
        print("\n Could not cross-validate codes. Ensure file naming contains master/history.")

if __name__ == "__main__":
    main()