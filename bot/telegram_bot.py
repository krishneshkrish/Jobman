# bot/telegram_bot.py — Telegram bot with proper command handling

import asyncio
import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logging.basicConfig(level=logging.WARNING)  # reduce noise

def authorized(update: Update) -> bool:
    return str(update.effective_chat.id) == str(TELEGRAM_CHAT_ID)

# ── /start ─────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    await update.message.reply_text(
        "<b>🤖 JobAgent is online!</b>\n\n"
        "I scan jobs daily and notify you. Here is what you can do:\n\n"
        "/scan — Scan for new jobs right now\n"
        "/status — Today's summary\n"
        "/pending — Jobs needing your attention\n"
        "/applied — Jobs auto-applied today\n"
        "/pause — Pause auto-applying\n"
        "/resume_agent — Resume auto-applying\n"
        "/help — Show this message",
        parse_mode="HTML"
    )

# ── /help ──────────────────────────────────────────────
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    await start(update, ctx)

# ── /scan ──────────────────────────────────────────────
async def scan_now(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    await update.message.reply_text("🔍 Scanning for new jobs... I will message you when done!")

    async def _run():
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from main import run_agent_cycle
            await run_agent_cycle(notify_telegram=True)
        except Exception as e:
            from telegram import Bot
            from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"❌ Scan error: {e}")

    asyncio.create_task(_run())

# ── /status ────────────────────────────────────────────
async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    from agent.tracker import get_today_summary
    summary = get_today_summary()

    msg = (
        f"<b>📊 Today's Summary</b>\n\n"
        f"✅ Auto-applied: {len(summary['auto_applied'])}\n"
        f"⏳ Pending your action: {len(summary['pending_manual'])}\n"
        f"📝 Total tracked: {summary['total']}"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

# ── /pending ───────────────────────────────────────────
async def pending(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    from agent.tracker import get_today_summary
    summary = get_today_summary()
    jobs = summary["pending_manual"]

    if not jobs:
        await update.message.reply_text("🎉 No pending jobs! All caught up.")
        return

    await update.message.reply_text(f"⏳ <b>{len(jobs)} jobs need your attention:</b>", parse_mode="HTML")

    for job in jobs[:5]:
        import os
        keyboard = [[
            InlineKeyboardButton("🔗 Open & Apply", url=job["url"]),
            InlineKeyboardButton("✅ Mark Applied", callback_data=f"done_{job.get('id', job['url'][:30])}"),
            InlineKeyboardButton("❌ Skip", callback_data=f"skip_{job.get('id', job['url'][:30])}"),
        ]]
        markup = InlineKeyboardMarkup(keyboard)
        score     = job.get("score", "?")
        one_liner = job.get("one_liner", "")
        msg = (
            f"📌 <b>{job['title']}</b>\n"
            f"🏢 {job['company']}\n"
            f"📍 {job.get('location', 'N/A')}\n"
            f"⭐ Match: {score}%\n"
            f"💡 <i>{one_liner}</i>"
        )
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=markup)

        # Send tailored resume as document
        resume_path = job.get("resume_path", "")
        if resume_path and os.path.exists(resume_path):
            with open(resume_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"Resume_{job['company'].replace(' ','_')}.txt",
                    caption=f"📄 Tailored resume for this role",
                )
        else:
            await update.message.reply_text("_No tailored resume found for this job._", parse_mode="Markdown")

    if len(jobs) > 5:
        await update.message.reply_text(f"<i>...and {len(jobs)-5} more. Showing top 5.</i>", parse_mode="HTML")

# ── /applied ───────────────────────────────────────────
async def applied_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    from agent.tracker import get_today_summary
    summary = get_today_summary()
    jobs = summary["auto_applied"]

    if not jobs:
        await update.message.reply_text("No auto-applications today yet.")
        return

    msg = "<b>✅ Auto-applied today:</b>\n\n"
    for job in jobs:
        msg += f"• *{job['title']}* @ {job['company']}\n"
    await update.message.reply_text(msg, parse_mode="HTML")

# ── /pause & /resume_agent ─────────────────────────────
async def pause(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    import config
    config.AUTO_APPLY_ENABLED = False
    await update.message.reply_text("⏸ Auto-applying paused. Use /resume_agent to turn back on.")

async def resume_agent(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not authorized(update): return
    import config
    config.AUTO_APPLY_ENABLED = True
    await update.message.reply_text("▶️ Auto-applying resumed!")

# ── Button callbacks ───────────────────────────────────
async def button_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("done_"):
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✅ Marked as applied!")
    elif data.startswith("skip_"):
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("❌ Skipped.")

# ── Notify helper (called by main agent) ───────────────
async def send_notification(bot: Bot, message: str, job: dict = None):
    if job and job.get("url"):
        keyboard = [[InlineKeyboardButton("🔗 Apply Now", url=job["url"])]]
        markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="Markdown",
            reply_markup=markup,
        )
    else:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode="Markdown",
        )

# ── Register commands with BotFather automatically ─────
async def set_bot_commands(app: Application):
    """Registers slash commands so they show up in Telegram UI."""
    from telegram import BotCommand
    commands = [
        BotCommand("start",        "Start the bot"),
        BotCommand("scan",         "Scan for new jobs now"),
        BotCommand("status",       "Today's summary"),
        BotCommand("pending",      "Jobs needing your attention"),
        BotCommand("applied",      "Jobs auto-applied today"),
        BotCommand("pause",        "Pause auto-applying"),
        BotCommand("resume_agent", "Resume auto-applying"),
        BotCommand("help",         "Show all commands"),
    ]
    await app.bot.set_my_commands(commands)
    print("[Telegram] Commands registered with BotFather ✅")

# ── Run bot ────────────────────────────────────────────
def run_bot():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",        start))
    app.add_handler(CommandHandler("help",         help_cmd))
    app.add_handler(CommandHandler("scan",         scan_now))
    app.add_handler(CommandHandler("status",       status))
    app.add_handler(CommandHandler("pending",      pending))
    app.add_handler(CommandHandler("applied",      applied_today))
    app.add_handler(CommandHandler("pause",        pause))
    app.add_handler(CommandHandler("resume_agent", resume_agent))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Auto-register commands on startup (no BotFather manual steps needed)
    app.post_init = set_bot_commands

    print("[Telegram] Bot is running... (Ctrl+C to stop)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    return app