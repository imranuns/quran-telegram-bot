# Quran Telegram Bot

A multi-functional Quran bot for Telegram that provides:
- 📖 Quran text by Surah and Juz
- 🔊 Audio links for specific reciters
- 👨‍💼 Admin features (status, broadcast)
- 🌐 Multi-language support (Amharic, English)

## Features

### User Commands
- `/start` - Welcome message and help
- `/surah <number>` - Get Surah text (1-114)
- `/juz <number>` - Get Juz text (1-30)
- `/abdulbasit <number>` - Audio recitation by Abdul Basit
- `/yasser <number>` - Audio recitation by Yasser Al-Dosari
- `/language` - Change language
- `/support <message>` - Send message to admin

### Admin Commands
- `/status` - Check total users and system status
- `/broadcast <message>` - Send message to all users
- `/debug` - Detailed debugging information

## Technology Stack

- **Language**: Python 3.x
- **Framework**: Flask
- **Hosting**: Vercel (serverless)
- **Database**: JSONBin.io
- **API**: Telegram Bot API

## Setup Instructions

### 1. Prerequisites

1. **Telegram Bot**: Create a bot via [@BotFather](https://t.me/BotFather) and get the token
2. **JSONBin Account**: Create a free account at [JSONBin.io](https://jsonbin.io/)
3. **Vercel Account**: Create account at [Vercel.com](https://vercel.com/)

### 2. JSONBin Setup

1. Log into JSONBin.io
2. Create a new bin with this initial content:
   ```json
   {
     "users": []
   }
   ```
3. Make sure the bin is **PUBLIC**
4. Note down your **API Key** and **Bin ID**

### 3. Environment Variables

Set these environment variables in Vercel:

```bash
TELEGRAM_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
JSONBIN_API_KEY=your_jsonbin_api_key
JSONBIN_BIN_ID=your_jsonbin_bin_id
CHANNEL_ID=@your_channel_username  # Optional
```

### 4. Local Testing

Before deploying to Vercel, test locally:

```bash
# Set environment variables
export TELEGRAM_TOKEN="your_token"
export ADMIN_ID="your_id"
export JSONBIN_API_KEY="your_key"
export JSONBIN_BIN_ID="your_bin_id"

# Run test script
python test_deployment.py

# Run locally (optional)
python api/index.py
```

### 5. Deploy to Vercel

1. Fork or clone this repository
2. Connect to Vercel
3. Set environment variables in Vercel dashboard
4. Deploy

### 6. Set Webhook

After deployment, set the Telegram webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-vercel-url.vercel.app/"}'
```

## Troubleshooting

### Database Issues

If `/status` shows "Total Users: 0":

1. **Check Environment Variables**:
   ```bash
   # Visit your deployed app at: https://your-app.vercel.app/test
   # This will show all environment variables and connection status
   ```

2. **Verify JSONBin Setup**:
   - Ensure bin is **PUBLIC**
   - Verify API key has read/write permissions
   - Check bin ID is correct

3. **Test JSONBin Manually**:
   ```bash
   # Test read access
   curl -H "X-Master-Key: YOUR_API_KEY" \
        https://api.jsonbin.io/v3/b/YOUR_BIN_ID
   ```

4. **Use Debug Command**:
   ```
   /debug  # Send this to your bot (admin only)
   ```

### Common Error Fixes

1. **403 Forbidden**: JSONBin API key is invalid
2. **404 Not Found**: JSONBin Bin ID is incorrect
3. **Empty Database**: Bin is private or malformed
4. **Webhook Issues**: Check Vercel logs

### Vercel Logs

Check Vercel function logs:
```bash
vercel logs your-deployment-url
```

### Test Endpoints

- **Health Check**: `https://your-app.vercel.app/`
- **Debug Info**: `https://your-app.vercel.app/test`

## File Structure

```
├── api/
│   └── index.py          # Main Flask application
├── test_deployment.py    # Local testing script
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - feel free to use and modify as needed.

## Support

If you encounter issues:

1. Run the test script: `python test_deployment.py`
2. Check the `/test` endpoint on your deployed app
3. Use the `/debug` command in Telegram (admin only)
4. Check Vercel function logs
5. Verify all environment variables are set correctly

---

**Note**: This bot is designed for educational and religious purposes. Please ensure you comply with Telegram's Terms of Service and any applicable laws in your region.