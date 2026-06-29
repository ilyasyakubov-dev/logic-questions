from datetime import datetime, date
from aiogram import Bot
from database.db import db_exec
from utils.translations import tr
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

log = logging.getLogger(__name__)

async def send_evening_reminders(bot: Bot):
    log.info("Running evening reminder job...")
    today_start = datetime.combine(date.today(), datetime.min.time()).isoformat()
    # Find registered users who have not answered any questions today
    users = await db_exec("""
        SELECT user_id, lang, first_name 
        FROM users 
        WHERE registered = 1 
          AND user_id NOT IN (
              SELECT DISTINCT user_id 
              FROM answered 
              WHERE answered_at >= ?
          )
    """, (today_start,))
    
    for u in users:
        try:
            lang = u["lang"]
            text = tr("evening_reminder", lang)
            await bot.send_message(u["user_id"], text)
            log.info(f"Sent reminder to user {u['user_id']}")
        except Exception as e:
            log.warning(f"Failed to send reminder to user {u['user_id']}: {e}")

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    # Add job to run daily at 20:00 (8:00 PM)
    scheduler.add_job(
        send_evening_reminders,
        "cron",
        hour=20,
        minute=0,
        args=[bot],
        id="evening_reminder_job",
        replace_existing=True
    )
    return scheduler
