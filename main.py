import os
import json
import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 設定 ---
# GitHub Secretsに登録した環境変数を読み込む
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
INTERVAL_MINUTES = 45  # 実行間隔（分）

def get_gspread_client():
    """環境変数からGoogle認証クライアントを作成"""
    if not GOOGLE_CREDENTIALS_JSON:
        raise ValueError("GOOGLE_CREDENTIALS environment variable is not set.")
    
    creds_info = json.loads(GOOGLE_CREDENTIALS_JSON)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)

def should_run(sheet):
    """
    スプレッドシートの最後の行のタイムスタンプを確認し、
    指定した間隔（45分）が経過しているか判定する
    """
    try:
        # A列にタイムスタンプが記録されていると仮定
        # 例: "2023-10-27 10:00:00"
        records = sheet.get_all_values()
        if len(records) < 2:  # ヘッダーしかない場合は実行
            return True
            
        last_time_str = records[-1][0]
        last_time = datetime.datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        
        diff = (now - last_time).total_seconds() / 60
        print(f"Last run: {last_time_str}. Minutes passed: {diff:.1f}")
        
        return diff >= (INTERVAL_MINUTES - 2) # わずかな誤差を許容
    except Exception as e:
        print(f"Check failed: {e}. Running anyway.")
        return True

def main():
    client = get_gspread_client()
    sh = client.open_by_key(SPREADSHEET_ID)
    worksheet = sh.get_worksheet(0) # 最初のシート

    # 45分経過チェック（厳密に管理したい場合）
    if not should_run(worksheet):
        print("Skipping run: Interval not reached yet.")
        return

    print("Running financial logger...")
    
    # --- ここに元のスクリプトのロジック（株価取得など）を記述 ---
    # 記録するデータの例
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    price = 150.25 # 本来は yfinance などで取得
    
    # シートに追記
    worksheet.append_row([timestamp, "USD/JPY", price])
    print("Done.")

if __name__ == "__main__":
    main()
