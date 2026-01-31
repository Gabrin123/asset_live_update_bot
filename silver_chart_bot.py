import os
import time
import requests
import schedule
from datetime import datetime
from flask import Flask
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Create a dummy web server for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Silver Bot with TradingView Screenshots is running!"

@app.route('/health')
def health():
    return "OK"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Telegram configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8355694996:AAE5aAFeeA1kFYiQIIe0coD_JdQQ3d6jROA')
CHAT_ID = os.environ.get('CHAT_ID', '-5232036612')

def get_chart_screenshot():
    """Capture TradingView chart screenshot using Selenium"""
    print("📸 Capturing TradingView screenshot...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = None
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # TradingView Silver 4H chart URL
        url = "https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=240"
        
        print(f"   Loading {url}")
        driver.get(url)
        
        # Wait for chart to load
        print("   Waiting for chart to render...")
        time.sleep(12)  # Give it time to fully load
        
        # Take screenshot
        screenshot_path = '/tmp/silver_chart.png'
        driver.save_screenshot(screenshot_path)
        
        print(f"   ✓ Screenshot saved!")
        
        return screenshot_path
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()

def send_photo_to_telegram(image_path, caption):
    """Send photo to Telegram chat"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    try:
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': CHAT_ID,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                print("✓ Chart sent to Telegram!")
                return True
            else:
                print(f"✗ Telegram error: {response.text}")
                return False
                
    except Exception as e:
        print(f"✗ Error sending photo: {e}")
        return False

def send_message_to_telegram(message):
    """Send text message to Telegram chat"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    try:
        data = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        print(f"✗ Error sending message: {e}")
        return False

def get_silver_price():
    """Get current silver price from Yahoo Finance"""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/SI=F"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            return price
            
        return None
        
    except Exception as e:
        print(f"✗ Error fetching price: {e}")
        return None

def job():
    """Main job - get price and send chart"""
    print(f"\n{'='*70}")
    print(f"🔔 SILVER UPDATE - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*70)
    
    # Get current silver price
    price = get_silver_price()
    
    if not price:
        print("⚠ Could not fetch price, skipping this cycle")
        return
    
    print(f"💰 Current Silver Price: ${price:.2f}")
    
    # Capture chart screenshot
    screenshot_path = get_chart_screenshot()
    
    if screenshot_path and os.path.exists(screenshot_path):
        # Send photo with price as caption
        caption = f"""📊 <b>Silver (XAG/USD) - 4 Hour Chart</b>

💰 Current Price: <b>${price:.2f}</b>
🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

<a href="https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=240">📈 View Live Chart on TradingView</a>
"""
        
        send_photo_to_telegram(screenshot_path, caption)
        
        # Clean up
        try:
            os.remove(screenshot_path)
        except:
            pass
    else:
        # Fallback: send text message if screenshot fails
        print("⚠ Screenshot failed, sending text message instead")
        
        message = f"""📊 <b>Silver Price Update</b>

💰 Current Price: <b>${price:.2f}</b>
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

📈 <a href="https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=240">View 4H Chart on TradingView</a>

<i>(Chart screenshot temporarily unavailable)</i>
"""
        
        send_message_to_telegram(message)
    
    print("✓ Update complete\n")

def main():
    """Main function to run the bot"""
    print("="*70)
    print("🤖 SILVER CHART BOT - STARTER TIER")
    print("="*70)
    
    # Start Flask FIRST (Render needs this)
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("✓ Flask web server started")
    
    # Give Flask 1 second to bind to port
    time.sleep(1)
    
    print(f"📱 Group Chat ID: {CHAT_ID}")
    print(f"⏰ Update Frequency: Every 3 minutes")
    print(f"📊 Chart: TradingView 4H (via Selenium)")
    
    # Send startup message ASAP
    print("\n📱 Sending startup notification...")
    try:
        send_message_to_telegram("🤖 Silver Bot started! First chart in 1 minute...")
        print("✓ Startup message sent")
    except Exception as e:
        print(f"✗ Error sending startup: {e}")
    
    # Schedule the job (don't run immediately to avoid timeout)
    schedule.every(3).minutes.do(job)
    
    # Wait a bit before first chart
    print("⏳ Waiting 60 seconds before first chart capture...")
    time.sleep(60)
    
    # Now run first chart
    print("🚀 Running first chart capture...")
    job()
    
    print("\n✓ Bot is now running normally...\n")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
