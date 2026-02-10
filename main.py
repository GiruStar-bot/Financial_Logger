import os
import json
import datetime
import gspread
import yfinance as yf
from google.oauth2.service_account import Credentials

# --- 設定 ---
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
INTERVAL_MINUTES = 45

# 取得したいティッカー（通貨ペアや株価）のリスト
# 元のプロジェクトに合わせて適宜変更してください
TICKERS = {
    "USD/JPY": "JPY=X",
    "Nikkei 225": "^N225",
    "S&P 500": "^GSPC",
    "Bitcoin": "BTC-USD"
}

def get_gspread_client():
    if not GOOGLE_CREDENTIALS_JSON:
        raise ValueError("Error: GOOGLE_CREDENTIALS is not set in GitHub Secrets.")
    
    try:
        creds_info = json.loads(GOOGLE_CREDENTIALS_JSON)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        raise ValueError(f"Error parsing JSON or authenticating: {e}")

def should_run(sheet):
    """前回の実行から45分経過しているか確認"""
    try:
        col_a = sheet.col_values(1)
        if len(col_a) < 2: return True # ヘッダーのみ
            
        last_time_str = col_a[-1]
        last_time = datetime.datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        
        diff = (now - last_time).total_seconds() / 60
        print(f"Checking interval... Last run: {last_time_str} ({diff:.1f} min ago)")
        
        return diff >= (INTERVAL_MINUTES - 5)
    except Exception as e:
        print(f"Interval check skipped (first run?): {e}")
        return True

def get_financial_data():
    """yfinanceを使用してデータを取得"""
    results = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results.append(timestamp)
    
    for name, symbol in TICKERS.items():
        try:
            ticker = yf.Ticker(symbol)
            # 最新の終値を取得
            price = ticker.history(period="1d")['Close'].iloc[-1]
            results.append(round(price, 2))
            print(f"Fetched {name}: {price}")
        except Exception as e:
            print(f"Failed to fetch {name}: {e}")
            results.append("N/A")
            
    return results

def main():
    if not SPREADSHEET_ID:
        raise ValueError("Error: SPREADSHEET_ID is missing.")

    print("Authenticating...")
    client = get_gspread_client()
    sh = client.open_by_key(SPREADSHEET_ID)
    worksheet = sh.get_worksheet(0)

    if not should_run(worksheet):
        print("Skipping: Interval of 45 minutes not yet reached.")
        return

    print("Fetching financial data...")
    data_row = get_financial_data()
    
    print("Recording to spreadsheet...")
    worksheet.append_row(data_row)
    print("Success!")

if __name__ == "__main__":
    main()
