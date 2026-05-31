# 🤖 JobAgent — Your Personal AI Job Application Assistant

Automated job hunting agent powered by Gemini, controlled via Telegram from your phone.

## What It Does
- Scrapes jobs daily from Naukri RSS, Remotive, Adzuna
- Scores each job against your resume using Gemini
- Tailors your resume per job description
- Auto-applies to Easy Apply jobs via Playwright
- Sends Telegram alerts for jobs needing your attention
- Tracks everything in Google Sheets

## Project Structure
```
job-agent/
├── agent/
│   ├── scraper.py          # Job discovery from multiple sources
│   ├── scorer.py           # Gemini-powered match scoring
│   ├── tailor.py           # Resume tailoring per JD
│   ├── applier.py          # Playwright auto-apply
│   └── tracker.py          # Google Sheets logging
├── bot/
│   └── telegram_bot.py     # Phone control interface
├── mcp_server/
│   └── server.py           # MCP server (Claude app integration)
├── data/
│   ├── resume.txt          # Your base resume (paste here)
│   └── applied_jobs.json   # Local cache
├── logs/
│   └── agent.log
├── config.py               # All settings in one place
├── main.py                 # Entry point - runs everything
├── scheduler.py            # Daily auto-run
└── requirements.txt
```

## Quick Start
1. Add your resume to `data/resume.txt`
2. Fill in `config.py` with your API keys
3. `pip install -r requirements.txt`
4. `playwright install chromium`
5. `python main.py`

## Phone Control (Telegram Commands)
- `/scan` — scan for new jobs now
- `/status` — today's summary
- `/applied` — list of jobs applied today
- `/pending` — jobs waiting for your attention
- `/pause` — pause auto-applying
- `/resume` — resume auto-applying
