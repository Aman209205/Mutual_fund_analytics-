import os
import requests
import pandas as pd

SCHEMES = {
    "125497": "HDFC_Top_100_Direct",
    "119551": "SBI_Bluechip",
    "120503": "ICICI_Bluechip",
    "118632": "Nippon_Large_Cap",
    "119092": "Axis_Bluechip",
    "120841": "Kotak_Bluechip"
}

def fetch_and_save_nav():
    print("Starting API data fetching...")
    all_nav_data = []
    
    for code, name in SCHEMES.items():
        print(f"Fetching data for: {name} ({code})...")
        url = f"https://api.mfapi.in/mf/{code}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                json_data = response.json()
                nav_list = json_data.get('data', [])
                
                df = pd.DataFrame(nav_list)
                df['scheme_code'] = code
                df['scheme_name'] = name
                all_nav_data.append(df)
            else:
                print(f"Failed for {code}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching {code}: {e}")
            
    if all_nav_data:
        final_df = pd.concat(all_nav_data, ignore_index=True)
        final_df = final_df[['scheme_code', 'scheme_name', 'date', 'nav']]
        
        #  FIX: Yeh line script ki actual location dhoondh kar folders apne aap bana degi
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.join(script_dir, "data", "raw")
        os.makedirs(target_dir, exist_ok=True)
        
        output_path = os.path.join(target_dir, "live_nav_history.csv")
        final_df.to_csv(output_path, index=False)
        print(f"\nSuccess! Saved live NAV data to {output_path}")
    else:
        print("No data was fetched.")

if __name__ == "__main__":
    fetch_and_save_nav()