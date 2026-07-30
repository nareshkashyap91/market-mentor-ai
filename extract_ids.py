import pandas as pd

def main():
    symbols = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "BHARTIARTL", "SBIN", "ITC", 
        "HINDUNILVR", "LT", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA", "TATAMOTORS", 
        "AXISBANK", "COALINDIA", "ADANIPORTS", "ASIANPAINT", "ULTRACEMCO", "JSWSTEEL", 
        "M&M", "TATASTEEL", "SIEMENS", "HAL", "TECHM", "PFC", "RECLTD", "BEL", "INDUSINDBK", 
        "CIPLA", "WIPRO", "DLF", "TRENT", "BPCL", "VBL", "HEROMOTOCO", "SHRIRAMFIN", 
        "POLYCAB", "PIDILITIND"
    ]
    
    print("Reading Dhan CSV...")
    df = pd.read_csv('https://images.dhan.co/api-data/api-scrip-master.csv', dtype=str)
    
    # Filter for NSE Equity symbols
    # SEM_EXM_EXCH_ID == 'NSE' and SEM_SERIES == 'EQ'
    # Let's print unique values of SEM_EXM_EXCH_ID and SEM_SERIES to verify
    print("Unique Exchanges:", df['SEM_EXM_EXCH_ID'].unique())
    
    nse_df = df[(df['SEM_EXM_EXCH_ID'] == 'NSE') & (df['SEM_SERIES'] == 'EQ')]
    print(f"Found {len(nse_df)} NSE EQ symbols.")
    
    mapping = {}
    for s in symbols:
        # Match symbol in SEM_TRADING_SYMBOL or SM_SYMBOL_NAME (without -EQ or trailing segments)
        match = nse_df[nse_df['SEM_TRADING_SYMBOL'] == s]
        if not match.empty:
            security_id = match['SEM_SMST_SECURITY_ID'].values[0]
            mapping[s] = security_id
        else:
            # Try fuzzy match in trading symbol
            match2 = nse_df[nse_df['SEM_TRADING_SYMBOL'].str.contains(s, na=False)]
            if not match2.empty:
                security_id = match2['SEM_SMST_SECURITY_ID'].values[0]
                mapping[s] = security_id
                print(f"Fuzzy matched {s} to {match2['SEM_TRADING_SYMBOL'].values[0]} : {security_id}")
            else:
                print(f"Could not find ID for {s}")
                
    print("\nMapping Result:")
    print(mapping)

if __name__ == '__main__':
    main()
