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

# Asset configurations
ASSETS = [
    {
        'name': 'Silver',
        'symbol': 'XAG/USD',
        'url': 'https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=240',
        'api_url': 'https://query1.finance.yahoo.com/v8/finance/chart/SI=F?interval=1m&range=1d',
        'price_range': (20, 100)
    },
    {
        'name': 'Gold',
        'symbol': 'XAU/USD',
        'url': 'https://www.tradingview.com/chart/?symbol=OANDA:XAUUSD&interval=240',
        'api_url': 'https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1m&range=1d',
        'price_range': (1500, 3000)
    },
    {
        'name': 'Bitcoin',
        'symbol': 'BTC/USD',
        'url': 'https://www.tradingview.com/chart/?symbol=BITSTAMP:BTCUSD&interval=240',
        'api_url': 'https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD?interval=1m&range=1d',
        'price_range': (10000, 150000)
    },
    {
        'name': 'Monero',
        'symbol': 'XMR/USD',
        'url': 'https://www.tradingview.com/chart/?symbol=KRAKEN:XMRUSD&interval=240',
        'api_url': 'https://query1.finance.yahoo.com/v8/finance/chart/XMR-USD?interval=1m&range=1d',
        'price_range': (50, 1000)
    }
]

def get_price_from_api(asset):
    """Get price from Yahoo Finance"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(asset['api_url'], headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            quotes = data['chart']['result'][0]['indicators']['quote'][0]
            close_prices = [p for p in quotes['close'] if p is not None]
            if close_prices:
                price = close_prices[-1]
                return price
    except Exception as e:
        print(f"   API error: {e}")
    return None

def get_chart_screenshot(asset):
    """Capture chart screenshot"""
    print(f"   📸 Capturing {asset['name']} screenshot...")
    
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
        driver.get(asset['url'])
        time.sleep(12)
        
        screenshot_path = f"/tmp/{asset['name'].lower()}_chart.png"
        driver.save_screenshot(screenshot_path)
        
        if os.path.exists(screenshot_path):
            print(f"   ✓ {asset['name']} screenshot saved")
            return screenshot_path
        
        return None
        
    except Exception as e:
        print(f"   ✗ Screenshot failed: {e}")
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
        print(f"   ✗ Send failed: {e}")
        return False

def send_message(text):
    """Send text message"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except:
        return False

def job():
    """Process all 4 assets and send consecutively"""
    try:
        print(f"\n{'='*60}")
        print(f"📊 UPDATE - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*60)
        
        # Process each asset one by one
        for i, asset in enumerate(ASSETS, 1):
            print(f"\n[{i}/4] Processing {asset['name']}...")
            
            # Get price
            price = get_price_from_api(asset)
            
            # Get screenshot
            screenshot_path = get_chart_screenshot(asset)
            
            if screenshot_path and os.path.exists(screenshot_path):
                # Create caption
                if price:
                    if asset['name'] == 'Bitcoin':
                        price_text = f"~${price:,.0f}"
                    else:
                        price_text = f"~${price:,.2f}"
                    price_note = " (see chart)"
                else:
                    price_text = "See chart"
                    price_note = ""
                
                caption = f"""📊 <b>{asset['name']} ({asset['symbol']}) - 4H</b>

💰 Price: <b>{price_text}</b>{price_note}
🕐 {datetime.now().strftime('%H:%M UTC')}"""
                
                # Send immediately
                print(f"   📤 Sending {asset['name']}...")
                if send_photo_to_telegram(screenshot_path, caption):
                    print(f"   ✓ {asset['name']} sent!")
                else:
                    print(f"   ✗ {asset['name']} send failed")
                
                # Cleanup
                try:
                    os.remove(screenshot_path)
                except:
                    pass
                
                # Small delay between messages (1 second)
                if i < len(ASSETS):
                    time.sleep(1)
            else:
                print(f"   ⚠ Skipping {asset['name']} - no screenshot")
        
        print("\n✓ All assets processed\n")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        print(traceback.format_exc())

def main():
    print("="*60)
    print("🤖 MULTI-ASSET CHART BOT (Sequential)")
    print("="*60)
    print("Assets: Silver, Gold, Bitcoin, Monero")
    print(f"Chat ID: {CHAT_ID}")
    print("="*60 + "\n")
    
    # Start Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("✓ Flask started\n")
    
    time.sleep(2)
    
    # Send startup
    send_message("🤖 Multi-Asset Bot started!\n\n📊 Silver, Gold, Bitcoin, Monero\n\nFirst charts in 1 minute...")
    
    # Schedule every 3 minutes
    schedule.every(3).minutes.do(job)
    
    # Wait 60 seconds then run first
    print("⏳ Waiting 60 seconds...")
    time.sleep(60)
    
    print("🚀 Running first update...\n")
    job()
    
    print("✓ Bot running\n")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL: {e}")
        import traceback
        print(traceback.format_exc())
        while True:
            time.sleep(60)
