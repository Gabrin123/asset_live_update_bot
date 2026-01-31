# Silver Chart Bot - Starter Tier Deployment Guide

## 📦 Files You Need

You have 3 files to upload to GitHub:
1. `silver_chart_bot.py` - Main bot code
2. `requirements.txt` - Python dependencies
3. `Dockerfile` - Docker configuration with Chrome

## 🚀 Step-by-Step Deployment

### Step 1: Create GitHub Repository

1. Go to https://github.com
2. Click the **"+"** icon (top right) → **"New repository"**
3. Name it: `silver-chart-bot`
4. Make it **Public** or **Private** (either works)
5. Click **"Create repository"**

### Step 2: Upload Files to GitHub

**Option A: Via Web Interface (Easier)**
1. In your new repo, click **"uploading an existing file"**
2. Drag and drop all 3 files:
   - `silver_chart_bot.py`
   - `requirements.txt`
   - `Dockerfile`
3. Click **"Commit changes"**

**Option B: Via Git Commands**
```bash
git clone https://github.com/YOUR_USERNAME/silver-chart-bot.git
cd silver-chart-bot
# Copy your 3 files here
git add .
git commit -m "Add silver bot files"
git push
```

### Step 3: Deploy on Render

1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect GitHub"** (authorize if needed)
4. Select your `silver-chart-bot` repository
5. Click **"Connect"**

### Step 4: Configure Service

**Basic Settings:**
- **Name**: `silver-bot` (or any name you like)
- **Region**: Choose closest to you
- **Branch**: `main` (or `master`)
- **Root Directory**: (leave blank)
- **Environment**: **Docker** ⚠️ IMPORTANT!

**Instance Type:**
- Select **"Starter"** ($7/month) ⚠️ REQUIRED for Chrome!
- DO NOT select Free tier - Chrome won't work

### Step 5: Add Environment Variables

Scroll down to **"Environment Variables"** section:

Click **"Add Environment Variable"** twice and add:

**Variable 1:**
- Key: `BOT_TOKEN`
- Value: `8355694996:AAE5aAFeeA1kFYiQIIe0coD_JdQQ3d6jROA`

**Variable 2:**
- Key: `CHAT_ID`
- Value: `-5232036612`

### Step 6: Deploy!

1. Click **"Create Web Service"** at the bottom
2. Wait 4-6 minutes for deployment (Chrome installation takes time)
3. Watch the logs - you should see:
   ```
   ============================================================
   🤖 SILVER CHART BOT - STARTER TIER
   ============================================================
   ✓ Flask web server started
   ✓ Bot is now running...
   ```

### Step 7: Verify It's Working

1. Check your Telegram group (ID: -5232036612)
2. You should receive:
   - Startup message immediately
   - First chart screenshot within 1 minute
   - Updates every 3 minutes after that

## 📊 What You'll Receive

Every 3 minutes in your Telegram group:
- 📸 TradingView 4H chart screenshot
- 💰 Current silver price (e.g., $32.45)
- 🕐 Timestamp
- 🔗 Link to live TradingView chart

## 💰 Cost

- **Render Starter Instance**: $7/month
- **Total**: $7/month (no other fees)

## 🔧 Troubleshooting

**If no messages appear:**
1. Check Render logs for errors
2. Verify environment variables are correct
3. Make sure bot token and chat ID are exact

**If you see "Chart screenshot temporarily unavailable":**
- Chrome might be taking longer to start
- Wait 1-2 more cycles, it should work after warmup

**To change update frequency:**
Edit line in `silver_chart_bot.py`:
```python
schedule.every(3).minutes.do(job)
```
Change `3` to any number of minutes

## 📝 Notes

- Bot runs 24/7, never sleeps
- Always-on with Starter tier
- Chrome and ChromeDriver included
- Automatic restarts on failure
- Your group chat ID: -5232036612

## ✅ Success Checklist

- [ ] Created GitHub repository
- [ ] Uploaded all 3 files
- [ ] Created Render web service
- [ ] Selected Docker environment
- [ ] Selected Starter instance ($7/month)
- [ ] Added BOT_TOKEN variable
- [ ] Added CHAT_ID variable
- [ ] Deployment successful
- [ ] Received startup message in Telegram
- [ ] Received first chart screenshot

---

**Need help?** Check Render logs or re-deploy if something goes wrong!
