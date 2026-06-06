# main.py — Orchestrates the full agent pipeline

import asyncio
import logging
from agent.scraper import scrape_all_jobs, save_seen_jobs
from agent.scorer import score_all_jobs
from agent.tailor import tailor_and_save
from agent.applier import apply_to_job
from agent.tracker import log_application
from config import AUTO_APPLY_ENABLED

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/agent.log"),
        logging.StreamHandler(),
    ]
)

async def run_agent_cycle(notify_telegram: bool = True):
    print("\n" + "="*50)
    print("🤖 JobAgent cycle starting...")
    print("="*50)

    # Step 1: Scrape
    new_jobs, seen = scrape_all_jobs()
    if not new_jobs:
        print("[Main] No new jobs found today.")
        if notify_telegram:
            await _notify("📭 No new jobs found today. I'll check again tomorrow!")
        return

    # Step 2: Score
    buckets = score_all_jobs(new_jobs)

    # Step 3: Auto-apply jobs — tailor resume + try applying
    applied_count = 0
    for job in buckets["auto_apply"]:
        print(f"\n[Main] Processing auto-apply: {job['title']} @ {job['company']}")
        resume_path = tailor_and_save(job)

        if AUTO_APPLY_ENABLED:
            success = await apply_to_job(job, resume_path)
            if success:
                applied_count += 1
                log_application(job, status="auto_applied", resume_path=resume_path)
                seen[job["id"]] = {"status": "auto_applied"}
            else:
                # Auto-apply failed → move to manual notify with resume ready
                buckets["notify"].insert(0, job)
                log_application(job, status="pending_manual", resume_path=resume_path)
                seen[job["id"]] = {"status": "pending_manual"}
        else:
            buckets["notify"].insert(0, job)
            log_application(job, status="pending_manual", resume_path=resume_path)
            seen[job["id"]] = {"status": "pending_manual"}

    # Step 4: Notify jobs — tailor resume for each so it's ready
    notify_jobs = buckets["notify"]
    for job in notify_jobs:
        if job["id"] not in seen:
            resume_path = tailor_and_save(job)
            log_application(job, status="pending_manual", resume_path=resume_path)
            seen[job["id"]] = {"status": "pending_manual"}

    # Step 5: Mark skipped as seen
    for job in buckets["skipped"]:
        seen[job["id"]] = {"status": "skipped"}

    save_seen_jobs(seen)

    # Step 6: Send Telegram summary + push top jobs WITH resumes
    if notify_telegram:
        await _send_summary_with_resumes(applied_count, notify_jobs, buckets["skipped"])

    print("\n✅ Agent cycle complete!")

async def _send_summary_with_resumes(applied: int, notify_jobs: list, skipped: list):
    try:
        from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
        import os

        bot = Bot(token=TELEGRAM_BOT_TOKEN)

        # ── Summary message ────────────────────────────
        msg = (
            f"<b>🤖 JobAgent Report</b>\n\n"
            f"✅ Auto-applied: {applied} jobs\n"
            f"⏳ Need your attention: {len(notify_jobs)} jobs\n"
            f"⏭ Skipped (low match): {len(skipped)} jobs\n"
        )
        if len(notify_jobs) > 3:
            msg += f"\n<i>Use /pending to see all jobs with apply buttons.</i>"

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=msg,
            parse_mode="HTML",
        )

        # ── Push top 5 jobs with tailored resume attached ─
        for job in notify_jobs[:5]:
            score    = job.get("score", "?")
            one_liner = job.get("one_liner", "")
            resume_path = job.get("resume_path") or _find_resume_for_job(job)

            # Job card with apply button
            keyboard = [[
                InlineKeyboardButton("🔗 Apply Now", url=job["url"]),
            ]]
            markup = InlineKeyboardMarkup(keyboard)

            card = (
                f"📌 *{job['title']}*\n"
                f"🏢 {job['company']}\n"
                f"📍 {job.get('location', 'N/A')}\n"
                f"⭐ Match: {score}%\n"
                f"💡 _{one_liner}_"
            )
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=card,
                parse_mode="HTML",
                reply_markup=markup,
            )

            # Send tailored resume as a document
            if resume_path and os.path.exists(resume_path):
                with open(resume_path, "rb") as f:
                    await bot.send_document(
                        chat_id=TELEGRAM_CHAT_ID,
                        document=f,
                        filename=f"Resume_{job['company'].replace(' ','_')}.txt",
                        caption=f"📄 Tailored resume for {job['title']} @ {job['company']}",
                    )

    except Exception as e:
        print(f"[Telegram] Notification failed: {e}")

def _find_resume_for_job(job: dict) -> str:
    """Fallback: find existing tailored resume file for a job."""
    import os, glob
    safe = f"{job['title']}_{job['company']}".replace(" ", "_").replace("/", "-")[:40]
    pattern = f"data/tailored_{safe}*.txt"
    matches = glob.glob(pattern)
    return matches[0] if matches else ""

async def _notify(message: str):
    try:
        from telegram import Bot
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"[Telegram] Notify failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_agent_cycle())