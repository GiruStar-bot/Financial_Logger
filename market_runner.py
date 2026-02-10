import requests
import yfinance as yf
from datetime import datetime

# --- ここにコピーしたURLを貼り付ける ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbySpuJWJ1AvgNcvxN6IHDQog-8GOJtYcj6Pb1cQFUO8jcK6Pg4fRGGnQo1dwzX-pIIb/exec"
# ------------------------------------

ASSETS = {
    'Nikkei225': '^N225',
    'USDJPY': 'JPY=X',
    'Bitcoin': 'BTC-USD'
}

def send_to_sheet():
    # 日本時間を簡易的に取得 (サーバー時間はUTCなので+9時間)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"--- {timestamp} データ送信開始 ---")

    tickers = list(ASSETS.values())
    try:
        market_data = yf.Tickers(' '.join(tickers))
        
        for name, symbol in ASSETS.items():
            try:
                ticker = market_data.tickers[symbol]
                price = ticker.fast_info.last_price
                
                if price:
                    # 送信するデータ
                    payload = {
                        'timestamp': timestamp,
                        'asset': name,
                        'price': round(price, 2)
                    }
                    
                    # スプレッドシートに送信 (POST)
                    response = requests.post(WEB_APP_URL, json=payload)
                    print(f"送信: {name} -> {response.text}")
                    
            except Exception as e:
                print(f"エラー ({name}): {e}")

    except Exception as e:
        print(f"全体エラー: {e}")

if __name__ == "__main__":
    send_to_sheet()
