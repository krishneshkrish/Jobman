# scheduler.py — Runs the agent daily + keeps Telegram bot alive

import asyncio
import schedule
import time
import threading
from config import SCAN_TIME
from main import run_agent_cycle
from bot.telegram_bot import run_bot

def run_schedule():
    """Schedules daily job scan."""
    schedule.every().day.at(SCAN_TIME).do(
        lambda: asyncio.run(run_agent_cycle(notify_telegram=True))
    )
    print(f"[Scheduler] Daily scan scheduled at {SCAN_TIME}")

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    print("🚀 JobAgent starting up...")

    # Run scheduler in background thread
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()

    # Run Telegram bot in main thread (blocking)
    run_bot()
