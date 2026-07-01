import pandas as pd
import os

def recommend_funds(risk_appetite, file_path='07_scheme_performance.csv'):
    if not os.path.exists(file_path):
        return "Error: Scheme performance dataset not found."
        
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.lower()
    
    risk_appetite = risk_appetite.strip().lower()
    
    risk_col = 'risk_grade' if 'risk_grade' in df.columns else df.columns[1]
    sharpe_col = 'sharpe_ratio' if 'sharpe_ratio' in df.columns else [c for c in df.columns if 'sharpe' in c.lower()][0]
    name_col = 'scheme_name' if 'scheme_name' in df.columns else df.columns[0]
    
    filtered = df[df[risk_col].astype(str).str.lower() == risk_appetite]
    top_3 = filtered.sort_values(by=sharpe_col, ascending=False).head(3)
    
    return top_3[[name_col, risk_col, sharpe_col]]

if __name__ == "__main__":
    import sys
    user_input = sys.argv[1] if len(sys.argv) > 1 else 'Moderate'
    print(f"--- Generating Top 3 Fund Recommendations for: {user_input} ---")
    print(recommend_funds(user_input))
