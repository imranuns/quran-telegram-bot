# 🕌 Quran Bot - Setup & Troubleshooting

## 🚨 Bot Stopped Issue - SOLUTION

Your Telegram Quran Bot has stopped because **environment variables are missing**. This is the most common cause of bot failures.

## 🔧 Quick Fix

### Step 1: Set Up Environment Variables

The bot requires these environment variables to function:

1. **TELEGRAM_TOKEN** - Get from [@BotFather](https://t.me/BotFather) on Telegram
2. **ADMIN_ID** - Your Telegram user ID (numeric)
3. **CHANNEL_ID** - Optional: Channel users must join (with @ prefix)
4. **JSONBIN_API_KEY** - Get from [JSONBin.io](https://jsonbin.io/)
5. **JSONBIN_BIN_ID** - Your JSONBin.io bin ID

### Step 2: Create Environment File

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual values
nano .env
```

### Step 3: Test Configuration

```bash
# Activate virtual environment
source venv/bin/activate

# Run setup script
python setup_bot.py
```

### Step 4: Start the Bot

```bash
# For local testing
python api/index.py

# For Vercel deployment
vercel deploy
```

## 📋 How to Get Required Credentials

### 1. Telegram Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Follow the instructions
4. Copy the token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Admin ID (Your Telegram User ID)
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your user ID (numeric)

### 3. JSONBin.io Setup
1. Sign up at [JSONBin.io](https://jsonbin.io/)
2. Create a new bin with this initial data:
   ```json
   {
     "users": {}
   }
   ```
3. Copy the Bin ID and API Key

### 4. Channel ID (Optional)
- If you want users to join a channel first, use the channel username with @ prefix
- Example: `@your_channel_name`

## 🧪 Testing Your Setup

Use the included setup script to test all connections:

```bash
python setup_bot.py
```

This will check:
- ✅ Environment variables
- ✅ Telegram Bot API connection
- ✅ JSONBin.io database connection  
- ✅ Quran API connection

## 🚀 Deployment Options

### Local Development
```bash
source venv/bin/activate
python api/index.py
```

### Vercel Deployment
1. Set environment variables in Vercel dashboard
2. Deploy: `vercel deploy`

### Other Platforms
Set the environment variables in your hosting platform's configuration.

## 🔍 Common Issues

### Bot Not Responding
- ✅ Check environment variables are set
- ✅ Verify Telegram token is correct
- ✅ Ensure bot is not blocked
- ✅ Check logs for errors

### Database Errors
- ✅ Verify JSONBin.io credentials
- ✅ Check bin exists and is accessible
- ✅ Ensure proper JSON structure

### API Failures
- ✅ Check internet connectivity
- ✅ Verify Quran API is accessible
- ✅ Check for rate limiting

## 📞 Support

If you need help:
1. Check the logs for specific error messages
2. Verify all environment variables are correctly set
3. Test each component individually using the setup script
4. Ensure your hosting platform supports the required dependencies

## 🛠️ Bot Features

Once properly configured, your bot supports:

- 📖 **Text Quran**: `/surah <number>` or `/juz <number>`
- 🔊 **Audio Recitations**: `/abdulbasit <number>` or `/yasser <number>`
- 🌐 **Multi-language**: Arabic, English, Amharic, Turkish
- 👥 **Channel Integration**: Optional forced channel membership
- 📊 **Admin Commands**: `/status`, `/broadcast`
- 🆘 **Support System**: `/support <message>`

## 🔐 Security Notes

- Never commit your `.env` file to version control
- Keep your bot token secret
- Regularly rotate your API keys
- Use environment variables for all sensitive data