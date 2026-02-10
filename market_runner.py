import requests
import yfinance as yf
from datetime import datetime, timedelta

# --- 設定 ---
# ※ここにあなたのWebアプリURLを貼り付けてください（ダブルクォーテーション " で囲むのを忘れずに！）
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbySpuJWJ1AvgNcvxN6IHDQog-8GOJtYcj6Pb1cQFUO8jcK6Pg4fRGGnQo1dwzX-pIIb/exec"

ASSETS = {
    'Nikkei225': '^N225',
    'USDJPY': 'JPY=X',
    'Bitcoin': 'BTC-USD',
    'SP500': '^GSPC'
}

def send_to_sheet():
    # GitHubサーバーはUTC(世界標準時)なので、日本時間(JST)にするために9時間足す
    jst_time = datetime.utcnow() + timedelta(hours=9)
    timestamp = jst_time.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"--- {timestamp} (JST) データ送信開始 ---")

    tickers = list(ASSETS.values())
    try:
        # yfinanceでデータ取得
        market_data = yf.Tickers(' '.join(tickers))
        
        for name, symbol in ASSETS.items():
            try:
                # fast_infoを使って高速に取得
                ticker = market_data.tickers[symbol]
                price = ticker.fast_info.last_price
                
                if price:
                    payload = {
                        'timestamp': timestamp,
                        'asset': name,
                        'price': round(price, 2)
                    }
                    
                    # スプレッドシートに送信
                    response = requests.post(WEB_APP_URL, json=payload)
                    print(f"送信成功: {name} -> {price}")
                    
            except Exception as e:
                print(f"個別エラー ({name}): {e}")

    except Exception as e:
        print(f"全体エラー: {e}")

if __name__ == "__main__":
    send_to_sheet()
