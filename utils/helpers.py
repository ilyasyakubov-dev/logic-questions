from datetime import date, timedelta
from database.db import db_exec, db_one

def week_start() -> str:
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()

async def add_score(user_id: int, pts: int):
    await db_exec("UPDATE users SET score = score + ? WHERE user_id=?", (pts, user_id))
    ws = week_start()
    await db_exec("""INSERT INTO weekly_scores (user_id,week_start,score) VALUES (?,?,?)
               ON CONFLICT(user_id,week_start) DO UPDATE SET score=score+?""",
            (user_id, ws, pts, pts))

async def get_lang(user_id: int) -> str:
    u = await db_one("SELECT lang FROM users WHERE user_id=?", (user_id,))
    return u["lang"] if u else "uz"
