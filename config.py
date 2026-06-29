import os
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DB_PATH = os.getenv("DB_PATH", "quizmaster.db")
