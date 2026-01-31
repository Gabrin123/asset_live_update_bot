import os
import sys
import time
import requests
import schedule
from datetime import datetime
from flask import Flask
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sys.stdout.flush()
sys.stderr.flush()

app = Flask(__name__)

@app.route('/')
def home():
    return "Multi-Asset Chart Bot Running"

@app.route('/health')
def health():
    return "OK"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8355694996:AAE5aAFeeA1kFYiQIIe0coD_JdQQ3d6jROA')
CHAT_ID = os.environ.get('CHAT_ID', '-5232036612')

def get_silver_price():
    """Get real-time silver price from Kitco"""
    try:
        # Try Kitco first (real-time spot price)
        url = "https://www.kitco.com/market/silver"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            import re
            # Look for spot price in the page
            matches = re.findall(r'Spot.*?(\d{2,3}\.\d{2})', response.text)
            if matches:
                price = float(matches[0])
                if 20 < price < 100:
                    print(f"   Kitco: ${price:.2f}")
                    return price
    except:
        pass
    
    # Fallback to Yahoo Finance
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/SI=F?interval=1m&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            quotes = data['chart']['result'][0]['indicators']['quote'][0]
            close_prices = [p for p in quotes['close'] if p is not None]
            if close_prices:
                print(f"   Yahoo: ${close_prices[-1]:.2f}")
                return close_prices[-1]
    except:
        pass
    return None

def get_gold_price():
    """Get real-time gold price"""
    try:
        # Try Kitco
        url = "https://www.kitco.com/market/gold"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            import re
            matches = re.findall(r'Spot.*?(\d{3,4}\.\d{2})', response.text)
            if matches:
                price = float(matches[0])
                if 1500 < price < 3000:
                    return price
    except:
        pass
    
    # Fallback
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1m&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            quotes = data['chart']['result'][0]['indicators']['quote'][0]
            close_prices = [p for p in quotes['close'] if p is not None]
            if close_prices:
                return close_prices[-1]
    except:
        pass
    return None

def get_bitcoin_price():
    """Get real-time Bitcoin price from CoinGecko"""
    try:
        # CoinGecko free API
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            price = data['bitcoin']['usd']
            return price
    except:
        pass
    
    # Fallback
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD?interval=1m&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            quotes = data['chart']['result'][0]['indicators']['quote'][0]
            close_prices = [p for p in quotes['close'] if p is not None]
            if close_prices:
                return close_prices[-1]
    except:
        pass
    return None

def get_monero_price():
    """Get real-time Monero price from CoinGecko"""
    try:
        # CoinGecko free API
        url = "https://api.coingecko.com/api/v3/simple/price?ids=monero&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            price = data['monero']['usd']
            return price
    except:
        pass
    
    # Fallback
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/XMR-USD?interval=1m&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            quotes = data['chart']['result'][0]['indicators']['quote'][0]
            close_prices = [p for p in quotes['close'] if p is not None]
            if close_prices:
                return close_prices[-1]
    except:
        pass
    return None

def get_chart_screenshot(url, name):
    """Capture chart screenshot"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0')
    
    driver = None
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(12)
        
        screenshot_path = f"/tmp/{name.lower()}_chart.png"
        driver.save_screenshot(screenshot_path)
        
        if os.path.exists(screenshot_path):
            return screenshot_path
        return None
        
    except Exception as e:
        print(f"Screenshot error for {name}: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()

def send_photo_to_telegram(image_path, caption):
    """Send photo to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    try:
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
            response = requests.post(url, files=files, data=data, timeout=30)
            return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def send_message_to_telegram(message):
    """Send text message"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except:
        return False

def job():
    """Main job - send all 4 charts"""
    print(f"\n{'='*60}")
    print(f"UPDATE - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*60)
    
    # Fetch all prices ONCE at the start
    print("\n📊 Fetching prices...")
    silver_price = get_silver_price()
    gold_price = get_gold_price()
    btc_price = get_bitcoin_price()
    xmr_price = get_monero_price()
    print(f"   Silver: ${silver_price:.2f}" if silver_price else "   Silver: Failed")
    print(f"   Gold: ${gold_price:,.2f}" if gold_price else "   Gold: Failed")
    print(f"   Bitcoin: ${btc_price:,.0f}" if btc_price else "   Bitcoin: Failed")
    print(f"   Monero: ${xmr_price:,.2f}" if xmr_price else "   Monero: Failed")
    
    # 1. SILVER
    print("\n1/4 Processing Silver...")
    silver_path = get_chart_screenshot("https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=240", "silver")
    
    if silver_path:
        price_text = f"~${silver_price:.2f} (see chart)" if silver_price else "See chart"
        caption = f"""📊 <b>Silver (XAG/USD) - 4H</b>

💰 Price: <b>{price_text}</b>
🕐 {datetime.now().strftime('%H:%M UTC')}"""
        send_photo_to_telegram(silver_path, caption)
        os.remove(silver_path)
        time.sleep(1)
    
    # 2. GOLD
    print("\n2/4 Processing Gold...")
    gold_path = get_chart_screenshot("https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD&interval=240", "gold")
    
    if gold_path:
        price_text = f"~${gold_price:,.2f} (see chart)" if gold_price else "See chart"
        caption = f"""📊 <b>Gold (XAU/USD) - 4H</b>

💰 Price: <b>{price_text}</b>
🕐 {datetime.now().strftime('%H:%M UTC')}"""
        send_photo_to_telegram(gold_path, caption)
        os.remove(gold_path)
        time.sleep(1)
    
    # 3. BITCOIN
    print("\n3/4 Processing Bitcoin...")
    btc_path = get_chart_screenshot("https://www.tradingview.com/chart/?symbol=BITSTAMP:BTCUSD&interval=240", "bitcoin")
    
    if btc_path:
        price_text = f"~${btc_price:,.0f} (see chart)" if btc_price else "See chart"
        caption = f"""📊 <b>Bitcoin (BTC/USD) - 4H</b>

💰 Price: <b>{price_text}</b>
🕐 {datetime.now().strftime('%H:%M UTC')}"""
        send_photo_to_telegram(btc_path, caption)
        os.remove(btc_path)
        time.sleep(1)
    
    # 4. MONERO
    print("\n4/4 Processing Monero...")
    xmr_path = get_chart_screenshot("https://www.tradingview.com/chart/?symbol=KRAKEN:XMRUSD&interval=240", "monero")
    
    if xmr_path:
        price_text = f"~${xmr_price:,.2f} (see chart)" if xmr_price else "See chart"
        caption = f"""📊 <b>Monero (XMR/USD) - 4H</b>

💰 Price: <b>{price_text}</b>
🕐 {datetime.now().strftime('%H:%M UTC')}"""
        send_photo_to_telegram(xmr_path, caption)
        os.remove(xmr_path)
    
    print("\n✓ Update complete\n")

def main():
    print("Multi-Asset Chart Bot Started")
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    time.sleep(2)
    
    send_message_to_telegram("🤖 Multi-Asset Bot started!\n\n📊 Silver, Gold, Bitcoin, Monero\n\nFirst charts in 1 minute...")
    
    schedule.every(3).minutes.do(job)
    
    time.sleep(60)
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
