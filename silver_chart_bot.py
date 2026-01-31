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

# Force unbuffered output
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

def get_chart_screenshot(asset):
    """Capture TradingView chart screenshot"""
    print(f"   📸 Capturing {asset['name']} chart...")
    
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
        time.sleep(12)  # Wait for chart to load
        
        screenshot_path = f"/tmp/{asset['name'].lower()}_chart.png"
        driver.save_screenshot(screenshot_path)
        
        if os.path.exists(screenshot_path):
            print(f"   ✓ {asset['name']} screenshot saved")
            return screenshot_path
        
        return None
        
    except Exception as e:
        print(f"   ✗ {asset['name']} screenshot failed: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()

def get_price_from_api(asset):
    """Get price from Yahoo Finance API"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(asset['api_url'], headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            quotes = data['chart']['result'][0]['indicators']['quote'][0]
            close_prices = [p for p in quotes['close'] if p is not None]
            if close_prices:
                price = close_prices[-1]
                print(f"   ✓ {asset['name']} API price: ${price:,.2f}")
                return price
    except Exception as e:
        print(f"   ✗ {asset['name']} API failed: {e}")
    
    return None

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
        print(f"   ✗ Telegram error: {e}")
        return False

def send_media_group(images_and_captions):
    """Send multiple photos as a media group"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMediaGroup"
    
    try:
        media = []
        files = {}
        
        for i, (image_path, caption) in enumerate(images_and_captions):
            attach_name = f"photo{i}"
            media.append({
                'type': 'photo',
                'media': f'attach://{attach_name}',
                'caption': caption,
                'parse_mode': 'HTML'
            })
            files[attach_name] = open(image_path, 'rb')
        
        data = {
            'chat_id': CHAT_ID,
            'media': str(media).replace("'", '"')
        }
        
        response = requests.post(url, data=data, files=files, timeout=60)
        
        # Close all file handles
        for f in files.values():
            f.close()
        
        if response.status_code == 200:
            print("   ✓ Media group sent!")
            return True
        else:
            print(f"   ✗ Media group failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ Media group error: {e}")
        return False

def job():
    """Main job - capture all charts and send together"""
    try:
        print(f"\n{'='*70}")
        print(f"📊 MULTI-ASSET UPDATE - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*70)
        
        charts_data = []
        
        # Process each asset
        for asset in ASSETS:
            print(f"\n🔄 Processing {asset['name']}...")
            
            # Get price from API
            price = get_price_from_api(asset)
            
            # Get chart screenshot
            screenshot_path = get_chart_screenshot(asset)
            
            if screenshot_path and os.path.exists(screenshot_path):
                # Create caption
                if price:
                    price_text = f"~${price:,.2f}"
                    price_note = " (see chart for exact)"
                else:
                    price_text = "See chart"
                    price_note = ""
                
                caption = f"""📊 <b>{asset['name']} ({asset['symbol']}) - 4H</b>
💰 Price: <b>{price_text}</b>{price_note}
🕐 {datetime.now().strftime('%H:%M UTC')}"""
                
                charts_data.append((screenshot_path, caption))
            else:
                print(f"   ⚠ Skipping {asset['name']} - no screenshot")
        
        # Send all charts as media group
        if charts_data:
            print(f"\n📤 Sending {len(charts_data)} charts as media group...")
            send_media_group(charts_data)
            
            # Cleanup
            for screenshot_path, _ in charts_data:
                try:
                    os.remove(screenshot_path)
                except:
                    pass
        else:
            print("   ⚠ No charts to send")
        
        print("\n✓ Update complete\n")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        print(traceback.format_exc())

def main():
    print("="*70)
    print("🤖 MULTI-ASSET CHART BOT")
    print("="*70)
    print("Step 1: Initializing...")
    print("Assets: Silver, Gold, Bitcoin, Monero")
    print(f"Chat ID: {CHAT_ID}")
    print(f"Frequency: Every 3 minutes")
    print("="*70 + "\n")
    
    # Start Flask
    print("Step 2: Starting Flask...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("✓ Flask started\n")
    
    time.sleep(2)
    
    # Send startup message
    print("Step 3: Sending startup message...")
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': CHAT_ID,
            'text': '🤖 Multi-Asset Bot started!\n\n📊 Tracking:\n• Silver\n• Gold\n• Bitcoin\n• Monero\n\nFirst charts in 1 minute...',
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✓ Startup message sent")
        else:
            print(f"✗ Startup message failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Startup message error: {e}")
    
    # Schedule
    print("\nStep 4: Setting up schedule...")
    schedule.every(3).minutes.do(job)
    print("✓ Schedule created")
    
    # Wait then run first job
    print("\nStep 5: Waiting 60 seconds before first update...")
    for i in range(6):
        time.sleep(10)
        print(f"   ... {(i+1)*10} seconds")
    
    print("\nStep 6: Running first update...")
    job()
    
    print("\n✓ Entering main loop...\n")
    
    loop_count = 0
    while True:
        schedule.run_pending()
        time.sleep(1)
        loop_count += 1
        if loop_count % 60 == 0:
            print(f"   [Loop alive: {loop_count//60} min]")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        print(traceback.format_exc())
        while True:
            time.sleep(60)
