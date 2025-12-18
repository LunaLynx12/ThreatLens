# Cybersecurity Discord Bot

A Discord bot that fetches cybersecurity news, CVEs, and generates AI-powered research project ideas.

## Features

- 📰 Fetch latest cybersecurity news from 20+ sources
- 🔖 Get CVE information from NIST NVD API
- 💡 Generate unique project ideas using Gemini AI
- 💾 Save and manage project ideas in SQLite database
- ✅ Track implementation status

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file:
```
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

3. Run the bot:
```bash
python bot.py
```

## Commands

- `!news [limit]` - Fetch cybersecurity news (1-10 items)
- `!cve [limit]` - Fetch CVE information (1-10 items)
- `!ideas` - Generate AI-powered project ideas
- `!saved [limit]` - View saved ideas
- `!implement <id>` - Mark idea as implemented
- `!help` - Show help

## License

MIT

