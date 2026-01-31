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
from selenium.webdriver.chrome.service import Service

# Force unbuffered output so logs show immediately
sys.stdout.flush()
sys.stderr.flush()

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

def extract_price_from_screenshot(image_path):
    """Extract current price from TradingView screenshot using OCR"""
    try:
        print("   🔍 Extracting price from screenshot with OCR...")
        
        # Try using pytesseract
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            # OCR the image
            text = pytesseract.image_to_string(img)
            
            # Look for price pattern in OCR text
            import re
            # TradingView shows price prominently at top
            matches = re.findall(r'(\d{2,3}\.\d{2,4})', text)
            
            if matches:
                # Get the first reasonable silver price
                for match in matches:
                    price = float(match)
                    if 20 < price < 100:  # Silver price range
                        print(f"   ✓ Extracted price from chart: ${price:.2f}")
                        return price
        except ImportError:
            print("   ⚠ pytesseract not available, skipping OCR")
        except Exception as e:
            print(f"   ⚠ OCR failed: {e}")
        
    except Exception as e:
        print(f"   ✗ Screenshot price extraction failed: {e}")
    
    return None

def get_chart_screenshot():
    """Capture TradingView chart screenshot using Selenium and extract price"""
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
    extracted_price = None
    
    try:
        print("   Starting Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        print("   ✓ Chrome started")
        
        # TradingView Silver 4H chart URL
        url = "https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=240"
        
        print(f"   Loading {url}")
        driver.get(url)
        print("   ✓ Page loaded")
        
        # Wait for chart to load
        print("   Waiting 12 seconds for chart to render...")
        time.sleep(12)
        
        # Try to extract price from page source
        try:
            print("   🔍 Extracting price from page...")
            import re
            page_source = driver.page_source
            
            # Look for price patterns in page source
            # TradingView embeds price in various places
            price_patterns = [
                r'"last":(\d{2,3}\.\d{2,4})',  # JSON data
                r'"close":(\d{2,3}\.\d{2,4})',  # Close price
                r'data-value="(\d{2,3}\.\d{2,4})"',  # Data attribute
                r'>(\d{2,3}\.\d{2,4})<',  # Direct text
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    for match in matches:
                        price = float(match)
                        if 20 < price < 100:  # Silver range
                            extracted_price = price
                            print(f"   ✓ Extracted price from page: ${price:.2f}")
                            break
                if extracted_price:
                    break
                    
        except Exception as e:
            print(f"   ⚠ Price extraction from page failed: {e}")
        
        # Take screenshot
        screenshot_path = '/tmp/silver_chart.png'
        print(f"   Taking screenshot to {screenshot_path}")
        driver.save_screenshot(screenshot_path)
        
        # Verify file was created
        if os.path.exists(screenshot_path):
            file_size = os.path.getsize(screenshot_path)
            print(f"   ✓ Screenshot saved! Size: {file_size} bytes")
            return screenshot_path, extracted_price
        else:
            print("   ✗ Screenshot file not found!")
            return None, None
        
    except Exception as e:
        print(f"   ✗ Error: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return None, None
        
    finally:
        if driver:
            print("   Closing Chrome...")
            try:
                driver.quit()
                print("   ✓ Chrome closed")
            except:
                print("   ⚠ Error closing Chrome")
                pass

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
    """Get current silver price from multiple sources"""
    
    print(f"   [Price fetch started at {datetime.now().strftime('%H:%M:%S')}]")
    
    # Try Yahoo Finance first
    try:
        print("   Trying Yahoo Finance...")
        url = "https://query1.finance.yahoo.com/v8/finance/chart/SI=F?interval=1m&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Try to get most recent 1-minute quote
            quotes = data['chart']['result'][0]['indicators']['quote'][0]
            close_prices = [p for p in quotes['close'] if p is not None]
            if close_prices:
                price = close_prices[-1]  # Most recent price
                print(f"   ✓ Yahoo Finance (1m): ${price:.2f}")
                return price
            # Fallback to regular market price
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            timestamp = data['chart']['result'][0]['meta'].get('regularMarketTime', 'unknown')
            print(f"   ✓ Yahoo Finance: ${price:.2f} (timestamp: {timestamp})")
            return price
    except Exception as e:
        print(f"   ✗ Yahoo Finance failed: {type(e).__name__}: {str(e)[:100]}")
    
    # Try alternative - live gold/silver API
    try:
        print("   Trying GoldAPI.io...")
        url = "https://www.goldapi.io/api/XAG/USD"
        headers = {"x-access-token": "goldapi-demo"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            price = data.get('price', 0)
            if price > 0:
                print(f"   ✓ GoldAPI: ${price:.2f}")
                return price
    except Exception as e:
        print(f"   ✗ GoldAPI failed: {type(e).__name__}: {str(e)[:100]}")
    
    # Try Kitco (most reliable, real-time)
    try:
        print("   Trying Kitco.com...")
        url = "https://www.kitco.com/market/silver"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            import re
            text = response.text
            # Kitco shows price prominently
            matches = re.findall(r'[\$]?(\d{2,3}\.\d{2})', text[:5000])  # Search first 5000 chars
            if matches:
                for match in matches:
                    price = float(match)
                    if 20 < price < 100:  # Silver range
                        print(f"   ✓ Kitco: ${price:.2f}")
                        return price
    except Exception as e:
        print(f"   ✗ Kitco failed: {type(e).__name__}: {str(e)[:100]}")
    
    # Try BullionVault (real-time spot)
    try:
        print("   Trying BullionVault...")
        url = "https://www.bullionvault.com/silver-price-chart.do"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            import re
            # Look for spot price
            matches = re.findall(r'spot.*?(\d{2,3}\.\d{2})', response.text, re.IGNORECASE)
            if matches:
                price = float(matches[0])
                if 20 < price < 100:
                    print(f"   ✓ BullionVault: ${price:.2f}")
                    return price
    except Exception as e:
        print(f"   ✗ BullionVault failed: {type(e).__name__}: {str(e)[:100]}")
    
    # All sources failed
    print("   ✗ All price sources failed")
    return None

def job():
    """Main job - get price and send chart"""
    try:
        print(f"\n{'='*70}")
        print(f"🔔 SILVER UPDATE - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print('='*70)
        
        # Get current silver price
        print("💰 Fetching silver price...")
        price = get_silver_price()
        
        if not price:
            print("⚠ Could not fetch price from APIs")
            # Use approximate price - silver typically ranges $28-$35
            # The chart image shows the exact price anyway
            price_text = "~$30-32 (see chart)"
            print(f"   Using placeholder: {price_text}")
        else:
            price_text = f"${price:.2f}"
            print(f"💰 Current Silver Price: ${price:.2f}")
        
        # Capture chart screenshot (returns screenshot_path AND extracted price)
        screenshot_path, chart_price = get_chart_screenshot()
        
        # Use chart price if available, otherwise API price
        if chart_price:
            price_text = f"${chart_price:.2f}"
            print(f"💰 Using exact price from TradingView: ${chart_price:.2f}")
        elif price:
            price_text = f"${price:.2f}"
            print(f"💰 Using API price: ${price:.2f}")
        else:
            price_text = "~$30-32 (see chart)"
            print(f"   Using placeholder: {price_text}")
        
        if screenshot_path and os.path.exists(screenshot_path):
            # Send photo with price as caption
            caption = f"""📊 <b>Silver (XAG/USD) - 4 Hour Chart</b>

💰 Price: <b>{price_text}</b>
🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

<a href="https://www.tradingview.com/chart/?symbol=TVC:SILVER&interval=240">📈 View Live Chart on TradingView</a>
"""
            
            print("📤 Sending chart to Telegram...")
            send_photo_to_telegram(screenshot_path, caption)
            
            # Clean up
            try:
                os.remove(screenshot_path)
                print("🗑️  Cleaned up screenshot file")
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
        
    except Exception as e:
        print(f"❌ ERROR in job(): {type(e).__name__}: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        send_message_to_telegram(f"❌ Error in silver bot: {str(e)}")

def log(msg):
    """Print with immediate flush"""
    print(msg, flush=True)
    sys.stdout.flush()

def main():
    """Main function to run the bot"""
    log("="*70)
    log("🤖 SILVER CHART BOT - STARTER TIER")
    log("="*70)
    log("Step 1: Starting...")
    
    # Start Flask FIRST (Render needs this)
    log("Step 2: Creating Flask thread...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("✓ Flask web server started")
    
    # Give Flask 1 second to bind to port
    print("Step 3: Waiting for Flask to bind...")
    time.sleep(1)
    print("✓ Flask should be ready")
    
    print(f"Step 4: Configuration:")
    print(f"   📱 Group Chat ID: {CHAT_ID}")
    print(f"   🤖 Bot Token: {BOT_TOKEN[:20]}...")
    print(f"   ⏰ Update Frequency: Every 3 minutes")
    print(f"   📊 Chart: TradingView 4H (via Selenium)")
    
    print("\nStep 5: Testing network connectivity...")
    try:
        test_response = requests.get("https://www.google.com", timeout=5)
        print(f"✓ Network test passed (status: {test_response.status_code})")
    except Exception as e:
        print(f"✗ Network test FAILED: {e}")
        print("⚠️ This may cause price fetching to fail!")
    
    # Send startup message ASAP
    print("\nStep 6: Sending startup notification...")
    try:
        result = send_message_to_telegram("🤖 Silver Bot started! First chart in 1 minute...")
        if result:
            print("✓ Startup message sent successfully")
        else:
            print("✗ Startup message failed")
    except Exception as e:
        print(f"✗ Error sending startup: {type(e).__name__}: {e}")
    
    # Schedule the job (don't run immediately to avoid timeout)
    print("\nStep 7: Setting up schedule...")
    schedule.every(3).minutes.do(job)
    print("✓ Schedule created (every 3 minutes)")
    
    # Wait a bit before first chart
    print("\nStep 8: Waiting 60 seconds before first chart capture...")
    for i in range(6):
        time.sleep(10)
        print(f"   ... {(i+1)*10} seconds elapsed")
    print("✓ Wait complete")
    
    # Now run first chart
    print("\nStep 9: Running first chart capture...")
    job()
    print("✓ First chart attempt complete")
    
    print("\nStep 10: Entering main loop...")
    print("✓ Bot is now running normally\n")
    
    loop_count = 0
    while True:
        schedule.run_pending()
        time.sleep(1)
        loop_count += 1
        if loop_count % 60 == 0:  # Print every minute
            print(f"   [Loop alive: {loop_count//60} minutes running]")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ FATAL ERROR IN MAIN:")
        print(f"{'='*70}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"\nFull traceback:")
        print(traceback.format_exc())
        print(f"{'='*70}\n")
        
        # Try to send error to Telegram
        try:
            send_message_to_telegram(f"❌ Silver bot crashed!\n\nError: {type(e).__name__}: {str(e)}")
        except:
            pass
        
        # Keep process alive so we can see logs
        print("Keeping process alive for debugging...")
        while True:
            time.sleep(60)
