# 🚀 Quick Setup Guide - Lakshya AI Trader

## 5-Minute Setup (Docker - Recommended)

### Step 1: Prerequisites
Ensure you have:
- Docker Desktop installed
- Docker Compose installed
- Telegram Bot Token (from @BotFather)
- Your Telegram User ID (from @userinfobot)

### Step 2: Clone & Configure
```bash
# Navigate to the project
cd lakshya_ai_trader

# Create environment file
cp .env.example .env

# Edit .env (use nano, vim, or any editor)
nano .env
```

### Step 3: Minimum Required Configuration
Add these to `.env`:
```env
# REQUIRED
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=your_telegram_user_id

# OPTIONAL (but recommended for full features)
OPENROUTER_API_KEY=sk-or-v1-xxxx    # Free from openrouter.ai
FINNHUB_API_KEY=xxxx                 # Free from finnhub.io
ALPHA_VANTAGE_API_KEY=xxxx           # Free from alphavantage.co
```

### Step 4: Launch
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f bot

# When you see "Bot started successfully!", you're good to go!
```

### Step 5: Test Your Bot
1. Open Telegram
2. Search for your bot (@YourBotName)
3. Send `/start`
4. Try `/quote RELIANCE`

## 🎯 Getting API Keys (All Free!)

### Telegram Bot Token (Required)
1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Follow prompts, choose bot name and username
4. Copy the token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Your Telegram User ID (Required for Admin)
1. Search for `@userinfobot` on Telegram
2. Start the bot
3. It will show your user ID (e.g., `123456789`)

### OpenRouter API Key (For AI Features)
1. Visit https://openrouter.ai/
2. Sign up (free)
3. Go to Keys section
4. Create new key
5. Copy and add to `.env`
6. **Benefit**: Free Gemini 2.0 Flash model for AI analysis

### Finnhub API Key (For News)
1. Visit https://finnhub.io/register
2. Sign up (free)
3. Dashboard will show your API key
4. Copy to `.env`
5. **Benefit**: 60 API calls/minute for stock news

### Alpha Vantage API Key (Backup Data Source)
1. Visit https://www.alphavantage.co/support/#api-key
2. Enter email, get instant key
3. Copy to `.env`
4. **Benefit**: 25 API calls/day as backup data source

## 🔧 Docker Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f bot

# Restart bot
docker-compose restart bot

# Check service status
docker-compose ps

# Rebuild after code changes
docker-compose up -d --build

# View database
docker-compose exec postgres psql -U postgres -d lakshya_trader

# Access Redis CLI
docker-compose exec redis redis-cli

# Remove all data and restart fresh
docker-compose down -v
docker-compose up -d
```

## 🐛 Troubleshooting

### Bot not starting?
```bash
# Check logs for errors
docker-compose logs bot

# Common issues:
# 1. Invalid bot token - check TELEGRAM_BOT_TOKEN in .env
# 2. Database connection - ensure postgres is running
# 3. Redis connection - ensure redis is running
```

### "Error fetching data" messages?
```bash
# Yahoo Finance is the primary source and works without API key
# If you see errors frequently:
# 1. Add ALPHA_VANTAGE_API_KEY to .env
# 2. Add FINNHUB_API_KEY to .env
```

### Database errors?
```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Wait 30 seconds for database to initialize
```

### Rate limit errors?
```bash
# Edit .env, increase limits:
RATE_LIMIT_PER_MINUTE=50
RATE_LIMIT_PER_DAY=1000

# Restart bot
docker-compose restart bot
```

## 📊 Verify Everything Works

Send these commands to your bot:

1. **Test Basic Functionality**
```
/start        # Should show welcome message
/help         # Should show command list
```

2. **Test Stock Data**
```
/quote RELIANCE    # Should show live price
RELIANCE           # Direct symbol input
/ta TCS            # Technical analysis
```

3. **Test AI (if configured)**
```
/ai RELIANCE       # AI-powered analysis
```

4. **Test Alerts**
```
/alert add RELIANCE above 3000
/alert list
```

5. **Test Watchlist**
```
/watchlist add RELIANCE
/watchlist add TCS
/watchlist
```

## 🎓 Feature Activation Checklist

- [ ] Bot Token configured → Bot responds to /start
- [ ] Admin ID configured → You can use admin commands
- [ ] OpenRouter API → AI analysis works
- [ ] Finnhub API → News fetching works
- [ ] Alpha Vantage API → Backup data source active
- [ ] Docker services running → All features operational

## 💡 Pro Tips

1. **For Development**:
   ```bash
   # Edit docker-compose.yml, set:
   DEBUG: true
   LOG_LEVEL: DEBUG
   ```

2. **For Production**:
   ```bash
   # Keep settings:
   ENVIRONMENT: production
   DEBUG: false
   LOG_LEVEL: INFO
   ```

3. **Backup Your Data**:
   ```bash
   # Backup database
   docker-compose exec postgres pg_dump -U postgres lakshya_trader > backup.sql
   
   # Restore database
   cat backup.sql | docker-compose exec -T postgres psql -U postgres lakshya_trader
   ```

4. **Monitor Resource Usage**:
   ```bash
   docker stats
   ```

5. **Update Bot**:
   ```bash
   git pull
   docker-compose up -d --build
   ```

## 🎯 Next Steps

Once your bot is running:

1. **Enable Daily Digest**:
   ```
   /digest on
   ```

2. **Create Your Watchlist**:
   ```
   /watchlist add RELIANCE
   /watchlist add TCS
   /watchlist add INFY
   ```

3. **Set Price Alerts**:
   ```
   /alert add RELIANCE above 2900
   ```

4. **Explore AI Features**:
   ```
   /ai RELIANCE
   Reliance abhi buy karna sahi hai?
   ```

5. **Check Scanner Results**:
   ```
   /scanner
   ```

## 🆘 Need Help?

- **Documentation**: See README.md
- **Logs**: `docker-compose logs -f bot`
- **Issues**: Check GitHub Issues
- **Community**: Join Telegram support group

## ✅ Success!

If you've completed all steps and the bot responds, congratulations! 🎉

Your Lakshya AI Trader bot is now live and ready to help with Indian stock market analysis.

Happy Trading! 📈
