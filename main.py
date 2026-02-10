import os
import json
import datetime
import re
import gspread
import yfinance as yf
from google.oauth2.service_account import Credentials

# --- 設定 ---
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS")
RAW_SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
INTERVAL_MINUTES = 45

# 日本時間のタイムゾーン定義 (UTC+9)
JST = datetime.timezone(datetime.timedelta(hours=9))

# --- 指標の追加はこちら ---
# 形式 -> "スプレッドシートでの表示名": "Yahoo Financeのシンボル"
TICKERS = {
    "USD/JPY": "JPY=X",          # 為替: ドル円
    "EUR/JPY": "EURJPY=X",       # 為替: ユーロ円
    "Nikkei 225": "^N225",       # 指数: 日経平均
    "TOPIX": "^TPX",             # 指数: TOPIX
    "S&P 500": "^GSPC",          # 指数: S&P 500
    "NASDAQ 100": "^NDX",        # 指数: NASDAQ 100
    "Bitcoin": "BTC-USD",        # 暗号資産: ビットコイン
    "Ethereum": "ETH-USD",       # 暗号資産: イーサリアム
    "Gold": "GC=F",              # 商品: 金先物
    "Crude Oil": "CL=F",         # 商品: 原油先物
    "Apple": "AAPL",             # 個別株: アップル
    "NVIDIA": "NVDA",            # 個別株: エヌビディア
}

def extract_spreadsheet_id(raw_id):
    if not raw_id:
        return None
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", raw_id)
    if match:
        return match.group(1)
    return raw_id

def get_gspread_client():
    if not GOOGLE_CREDENTIALS_JSON:
        raise ValueError("Error: GOOGLE_CREDENTIALS is not set.")
    
    try:
        creds_info = json.loads(GOOGLE_CREDENTIALS_JSON)
        print(f"Auth: Using service account -> {creds_info.get('client_email')}")
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        raise ValueError(f"Error parsing JSON or authenticating: {e}")

def should_run(sheet):
    """日本時間（JST）で前回からの経過時間を判定"""
    try:
        col_a = sheet.col_values(1)
        if len(col_a) < 2: 
            print("Time check: Sheet is empty. Starting first log.")
            return True
            
        last_time_str = col_a[-1]
        try:
            last_time = datetime.datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST)
        except ValueError:
            print(f"Time check: Could not parse '{last_time_str}'. Running anyway.")
            return True

        now = datetime.datetime.now(JST)
        diff = (now - last_time).total_seconds() / 60
        print(f"Time check: Last run was {diff:.1f} minutes ago (JST).")
        
        if diff < 0:
            print("Time check: Detected timezone mismatch or future timestamp. Running to reset.")
            return True

        return diff >= (INTERVAL_MINUTES - 2)
    except Exception as e:
        print(f"Time check error (ignored): {e}")
        return True

def get_financial_data():
    results = []
    timestamp = datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    results.append(timestamp)
    
    print(f"Fetching {len(TICKERS)} indicators...")
    for name, symbol in TICKERS.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                results.append(round(float(price), 2))
                print(f"  OK: {name} -> {price:.2f}")
            else:
                results.append("N/A")
                print(f"  NO DATA: {name}")
        except Exception as e:
            print(f"  FAILED: {name} ({e})")
            results.append("Error")
            
    return results

def main():
    spreadsheet_id = extract_spreadsheet_id(RAW_SPREADSHEET_ID)
    if not spreadsheet_id:
        raise ValueError("Error: SPREADSHEET_ID is missing.")

    try:
        print("--- Step 1: Authentication ---")
        client = get_gspread_client()
        
        print(f"--- Step 2: Open Spreadsheet (ID: {spreadsheet_id}) ---")
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)

        print("--- Step 3: Check Interval (JST Based) ---")
        if not should_run(worksheet):
            print("Skipping: Interval of 45 minutes not yet reached.")
            return

        print("--- Step 4: Fetch Data ---")
        data_row = get_financial_data()
        
        print("--- Step 5: Record to Spreadsheet ---")
        worksheet.append_row(data_row)
        print(f"Success! Recorded at JST: {data_row[0]}")

    except gspread.exceptions.PermissionError:
        print("\n[!] ERROR: Permission Denied. Share the sheet with the email in Step 1.")
    except Exception as e:
        print(f"\n[!] UNEXPECTED ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
