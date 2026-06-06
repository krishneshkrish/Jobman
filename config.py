# config.py — All settings in one place
import os

# ── Gemini ─────────────────────────────────────────────
#GEMINI_API_KEY = "xxxxxxxx"          # aistudio.google.com
#GEMINI_MODEL   = "gemini-3.5-flash"             # Free tier, fast

#OPENROUTER_API_KEY = "API KEy"  # openrouter.ai/keys
# Free models — pick one below (uncomment your choice):
#OPENROUTER_MODEL = "openrouter/auto"   # Fast, good quality
# OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"    # Alternative
# OPENROUTER_MODEL = "google/gemma-3-12b-it:free"            # Google's free model
 

# ── Telegram ───────────────────────────────────────────
#TELEGRAM_BOT_TOKEN  = "token"          # @BotFather on Telegram
#TELEGRAM_CHAT_ID    = "ID"            # @userinfobot to get this
# ── OpenRouter ─────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.environ.get("OPENROUTER_MODEL", "openrouter/auto")

# ── Telegram ───────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# ── Google Sheets (optional tracker) ───────────────────
GOOGLE_SHEETS_CREDS = "credentials.json"        # From Google Cloud Console
SPREADSHEET_ID      = "YOUR_SPREADSHEET_ID"

# ── Job Search Keywords ────────────────────────────────
KEYWORDS_POWER_PLATFORM = [
    "Power Platform Developer",
    "Power Apps Developer",
    "Power Automate Developer",
    "Low Code Developer",
    "RPA Developer",
    "Business Automation Developer",
]
 
KEYWORDS_AI = [
    "AI Engineer",
    "ML Engineer",
    "Prompt Engineer",
    "AI Agent Developer",
    "LLM Application Developer",
    "RAG Developer",
    "LangChain Developer",
    "LangGraph Developer",
    "Generative AI Developer",
    "AI Automation Engineer",
]
 
JOB_KEYWORDS = KEYWORDS_POWER_PLATFORM + KEYWORDS_AI
 
# ── Location Preferences ───────────────────────────────
# Jobs in these cities/regions are PREFERRED (higher score bonus)
PREFERRED_LOCATIONS = [
    "Trivandrum", "Thiruvananthapuram",
    "Kochi", "Cochin", "Ernakulam",
    "Kozhikode", "Calicut",
    "Kerala",
    "Remote", "Work from Home", "WFH",
]
 
# Jobs in these cities are ACCEPTABLE (no penalty)
ACCEPTABLE_LOCATIONS = [
    "Bangalore", "Bengaluru",
    "Chennai",
    "Hyderabad",
    "Pune",
    "Mumbai",
    "India",                 # unspecified India is fine
]
 
# Jobs ONLY in these cities get auto-skipped by scorer
SKIP_LOCATIONS = [
    "Noida", "Delhi", "Gurgaon", "Gurugram", "NCR",
    "Kolkata", "Ahmedabad", "Jaipur",
    "USA", "UK", "Brazil", "Australia", "Canada",
    "Bulgaria", "Europe",
]
 
# ── Experience & Seniority ─────────────────────────────
EXPERIENCE_YEARS    = 1
MAX_EXPERIENCE_REQ  = 2     # Skip jobs requiring more than this
 
# ── Scoring Thresholds ─────────────────────────────────
AUTO_APPLY_THRESHOLD = 80
NOTIFY_THRESHOLD     = 60
SKIP_THRESHOLD       = 60
 
# ── Scheduler ──────────────────────────────────────────
SCAN_TIME = "08:00"
 
# ── Safety ─────────────────────────────────────────────
MAX_DAILY_APPLICATIONS = 15
AUTO_APPLY_ENABLED     = True
