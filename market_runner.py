import pandas as pd
import yfinance as yf
from datetime import datetime
import os

# 取得対象
ASSETS = {
    'Nikkei225': '^N225',
    'USDJPY': 'JPY=X',
    'Bitcoin': 'BTC-USD',
    'SP500': '^GSPC'
}

CSV_FILE = 'market_data.csv'

def fetch_and_save():
    data_records = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"--- {timestamp} データ取得開始 ---")

    # データ取得 (まとめて取得して効率化)
    tickers = list(ASSETS.values())
    try:
        # yfinanceでデータ取得
        market_data = yf.Tickers(' '.join(tickers))
        
        for name, symbol in ASSETS.items():
            try:
                # 直近の価格を取得
                ticker = market_data.tickers[symbol]
                price = ticker.fast_info.last_price
                
                if price:
                    record = {
                        'timestamp': timestamp,
                        'asset': name,
                        'price': round(price, 2)
                    }
                    data_records.append(record)
                    print(f"取得成功: {name} = {price}")
            except Exception as e:
                print(f"エラー ({name}): {e}")

    except Exception as e:
        print(f"全体エラー: {e}")
        return

    # CSVへの保存処理
    if data_records:
        df_new = pd.DataFrame(data_records)
        
        # ファイルが既に存在すれば読み込んで追記、なければ新規作成
        if os.path.exists(CSV_FILE):
            try:
                # 既存のCSVを読み込む（エラー回避のため空の場合は無視）
                df_existing = pd.read_csv(CSV_FILE)
                df_final = pd.concat([df_existing, df_new], ignore_index=True)
            except pd.errors.EmptyDataError:
                df_final = df_new
        else:
            df_final = df_new
            
        # 保存
        df_final.to_csv(CSV_FILE, index=False)
        print("CSV保存完了")
    else:
        print("新規データなし")

if __name__ == "__main__":
    fetch_and_save()
