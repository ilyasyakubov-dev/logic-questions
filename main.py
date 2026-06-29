import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import db_init, db_seed
from handlers import get_handlers_router
from utils.scheduler import setup_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger(__name__)

async def main():
    # 1. Initialize Database & Seed
    await db_init()
    await db_seed()

    # 2. Initialize Bot and Dispatcher
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # 3. Register Handlers Router
    dp.include_router(get_handlers_router())

    # 4. Setup and start APScheduler
    scheduler = setup_scheduler(bot)
    scheduler.start()
    log.info("⏰ APScheduler eslatma vazifalari ishga tushdi.")

    # 5. Start Polling
    log.info("🚀 QuizMaster Bot (Modulli) polling rejimida ishga tushmoqda...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        # Shutdown scheduler safely
        scheduler.shutdown()
        log.info("🔒 Bot va Scheduler to'xtatildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot stopped.")
