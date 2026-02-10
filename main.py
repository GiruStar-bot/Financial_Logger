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

# 取得したいティッカー（通貨ペアや株価）
TICKERS = {
    "USD/JPY": "JPY=X",
    "Nikkei 225": "^N225",
    "S&P 500": "^GSPC",
    "Bitcoin": "BTC-USD"
}

def extract_spreadsheet_id(raw_id):
    """URLが渡された場合でもID部分だけを抜き出す"""
    if not raw_id:
        return None
    # URL形式(https://docs.google.com/spreadsheets/d/ID/...)からIDを抽出
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", raw_id)
    if match:
        return match.group(1)
    return raw_id # すでにID形式ならそのまま返す

def get_gspread_client():
    if not GOOGLE_CREDENTIALS_JSON:
        raise ValueError("Error: GOOGLE_CREDENTIALS is not set in GitHub Secrets.")
    
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
    """前回の実行から指定時間が経過しているか確認"""
    try:
        col_a = sheet.col_values(1)
        if len(col_a) < 2: 
            print("Time check: Sheet is empty or header only. Starting first log.")
            return True
            
        last_time_str = col_a[-1]
        try:
            last_time = datetime.datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"Time check: Could not parse date '{last_time_str}'. Running anyway.")
            return True

        now = datetime.datetime.now()
        diff = (now - last_time).total_seconds() / 60
        print(f"Time check: Last run was {diff:.1f} minutes ago.")
        
        return diff >= (INTERVAL_MINUTES - 2)
    except Exception as e:
        print(f"Time check error (ignored): {e}")
        return True

def get_financial_data():
    """yfinanceを使用してデータを取得。失敗しても止まらないようにする"""
    results = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results.append(timestamp)
    
    for name, symbol in TICKERS.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                results.append(round(float(price), 2))
                print(f"Fetched {name}: {price}")
            else:
                print(f"No data for {name}")
                results.append("N/A")
        except Exception as e:
            print(f"Failed to fetch {name}: {e}")
            results.append("Error")
            
    return results

def main():
    spreadsheet_id = extract_spreadsheet_id(RAW_SPREADSHEET_ID)
    if not spreadsheet_id:
        raise ValueError("Error: SPREADSHEET_ID is missing from GitHub Secrets.")

    try:
        print("--- Step 1: Authentication ---")
        client = get_gspread_client()
        
        print(f"--- Step 2: Open Spreadsheet (ID: {spreadsheet_id}) ---")
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)

        print("--- Step 3: Check Interval ---")
        if not should_run(worksheet):
            print("Skipping: Interval of 45 minutes not yet reached.")
            return

        print("--- Step 4: Fetch Data ---")
        data_row = get_financial_data()
        
        print("--- Step 5: Record to Spreadsheet ---")
        worksheet.append_row(data_row)
        print(f"Success! Recorded: {data_row}")

    except gspread.exceptions.PermissionError:
        print("\n[!] ERROR: Permission Denied.")
        print("Please share your Google Sheet with the service account email shown in Step 1.")
    except gspread.exceptions.SpreadsheetNotFound:
        print("\n[!] ERROR: Spreadsheet not found.")
        print(f"Double check your ID: {spreadsheet_id}")
    except Exception as e:
        print(f"\n[!] UNEXPECTED ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
