# pyrefly: ignore [missing-import]
import aiosqlite
import logging
import os
from config import DB_PATH

# Ensure parent directory of DB_PATH exists
db_dir = os.path.dirname(DB_PATH)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

log = logging.getLogger(__name__)

SEED_QUESTIONS = [
    # ── MATH ──────────────────────────────────────────────────
    # UZ
    ("math","uz","choice","2 × 2 = ?","3","4","5","B","Matematikaning asosi — ko'paytirish jadvalidir.",1),
    ("math","uz","choice","10 ning kvadrat ildizi nechaga teng?","√10 ≈ 3.16","10","100","A","√10 ≈ 3.162, irratsional son.",2),
    ("math","uz","open","5 faktorial (5!) nechaga teng?",None,None,None,"120","5! = 5×4×3×2×1 = 120",1),
    ("math","uz","choice","π ning taxminiy qiymati qanday?","3.14","2.71","1.41","A","π — doira aylanasi uzunligining diametriga nisbati.",1),
    ("math","uz","open","Uchburchak ichki burchaklarining yig'indisi necha gradus?",None,None,None,"180","Euklidov geometriyasida har qanday uchburchak uchun.",1),
    # RU
    ("math","ru","choice","Чему равно 7 × 8?","54","56","58","B","7×8=56 — классика таблицы умножения.",1),
    ("math","ru","choice","Сколько нулей в числе миллиард?","6","8","9","C","1 000 000 000 — девять нулей.",1),
    ("math","ru","open","Чему равен корень из 144?",None,None,None,"12","√144 = 12, так как 12² = 144.",1),
    # EN
    ("math","en","choice","What is 15% of 200?","25","30","40","B","15% of 200 = 0.15 × 200 = 30.",1),
    ("math","en","open","What is the value of 2 to the power of 10?",None,None,None,"1024","2^10 = 1024 — useful in computing (1 KB).",2),
    # ── HISTORY ───────────────────────────────────────────────
    ("history","uz","choice","O'zbekiston qachon mustaqillikka erishdi?","1990","1991","1992","B","1991-yil 1-sentabrda mustaqillik e'lon qilindi.",1),
    ("history","uz","choice","Amir Temur qayerda tug'ilgan?","Buxoro","Samarqand","Kesh (Shahrisabz)","C","Temur 1336-yilda Kesh (hozirgi Shahrisabz)da tug'ilgan.",1),
    ("history","uz","open","O'zbekistonning poytaxti qaysi shahar?",None,None,None,"toshkent","Toshkent — Markaziy Osiyoning eng yirik shahri.",1),
    ("history","ru","choice","В каком году была основана Москва?","1147","1200","1380","A","Москва основана в 1147 году Юрием Долгоруким.",1),
    ("history","ru","open","Кто написал 'Войну и мир'?",None,None,None,"толстой","Лев Николаевич Толстой написал этот роман-эпопею.",1),
    ("history","en","choice","Who was the first President of the United States?","Thomas Jefferson","George Washington","Abraham Lincoln","B","George Washington served 1789–1797.",1),
    ("history","en","open","In which year did World War II end?",None,None,None,"1945","WWII ended in 1945: VE Day (May 8) and VJ Day (Sep 2).",1),
    # ── SCIENCE ───────────────────────────────────────────────
    ("science","uz","choice","Yorug'likning vakuumdagi tezligi necha km/s?","200 000","300 000","150 000","B","c ≈ 299 792 km/s — tabiatdagi eng katta tezlik.",1),
    ("science","uz","open","Suvning kimyoviy formulasi nima?",None,None,None,"h2o","H₂O — ikki vodorod, bir kislorod atomi.",1),
    ("science","uz","choice","DNK nimani anglatadi?","Dezoksiribonuklein kislota","Dinitrogen kislota","Difosfor kislota","A","DNK — genetik ma'lumotni saqlaydi.",2),
    ("science","ru","choice","Какой газ составляет большую часть атмосферы Земли?","Кислород","Азот","Углекислый газ","B","Азот составляет около 78% атмосферы.",1),
    ("science","ru","open","Сколько костей у взрослого человека?",None,None,None,"206","У взрослого человека 206 костей.",2),
    ("science","en","choice","What planet is known as the Red Planet?","Venus","Jupiter","Mars","C","Mars appears red due to iron oxide on its surface.",1),
    ("science","en","open","What is the chemical symbol for gold?",None,None,None,"au","Au comes from the Latin word 'Aurum'.",1),
    # ── GENERAL ───────────────────────────────────────────────
    ("general","uz","choice","Dunyo bo'yicha eng ko'p so'zlashadigan til qaysi?","Ingliz tili","Mandarin (Xitoy) tili","Ispan tili","B","Mandarin — 1 mlrd dan ortiq ona tilida so'zlashuvchilar.",1),
    ("general","uz","open","Olimpiya o'yinlari necha yilda bir marta o'tkaziladi?",None,None,None,"4","Yozgi va Qishki Olimpiada har 4 yilda bo'lib o'tadi.",1),
    ("general","uz","choice","Sahara cho'li qaysi qit'ada joylashgan?","Osiyo","Amerika","Afrika","C","Sahara — dunyodagi eng katta issiq cho'l.",1),
    ("general","ru","choice","Какая самая длинная река в мире?","Амазонка","Нил","Янцзы","B","Нил — длиной около 6650 км.",1),
    ("general","ru","open","Сколько цветов у радуги?",None,None,None,"7","Красный, оранжевый, жёлтый, зелёный, голубой, синий, фиолетовый.",1),
    ("general","en","choice","How many continents are there on Earth?","5","6","7","C","The 7 continents: Africa, Antarctica, Asia, Australia, Europe, North America, South America.",1),
    ("general","en","open","What is the capital of Japan?",None,None,None,"tokyo","Tokyo is the capital and most populous city of Japan.",1),
    ("general","en","choice","Which ocean is the largest?","Atlantic","Indian","Pacific","C","The Pacific Ocean covers about 165 million km².",1),
]

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            last_name   TEXT,
            phone       TEXT,
            lang        TEXT DEFAULT 'uz',
            score       INTEGER DEFAULT 0,
            correct_cnt INTEGER DEFAULT 0,
            wrong_cnt   INTEGER DEFAULT 0,
            streak      INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            last_daily  TEXT,
            registered  INTEGER DEFAULT 0,
            joined_at   TEXT
        );
        CREATE TABLE IF NOT EXISTS questions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT NOT NULL,
            lang        TEXT NOT NULL DEFAULT 'uz',
            q_type      TEXT NOT NULL,       -- 'choice' or 'open'
            question    TEXT NOT NULL,
            option_a    TEXT,
            option_b    TEXT,
            option_c    TEXT,
            answer      TEXT NOT NULL,
            explanation TEXT,
            difficulty  INTEGER DEFAULT 1    -- 1=easy 2=medium 3=hard
        );
        CREATE TABLE IF NOT EXISTS weekly_scores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            week_start  TEXT,
            score       INTEGER DEFAULT 0,
            UNIQUE(user_id, week_start)
        );
        CREATE TABLE IF NOT EXISTS achievements (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            code        TEXT,
            earned_at   TEXT,
            UNIQUE(user_id, code)
        );
        CREATE TABLE IF NOT EXISTS answered (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            question_id INTEGER,
            is_correct  INTEGER,
            answered_at TEXT
        );
        """)
        await db.commit()
    log.info("Database initialized (Async).")

async def db_exec(sql: str, params: tuple = ()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            await db.commit()
            return [dict(r) for r in rows]

async def db_one(sql: str, params: tuple = ()):
    rows = await db_exec(sql, params)
    return rows[0] if rows else None

async def db_seed():
    existing = await db_one("SELECT COUNT(*) as cnt FROM questions")
    if existing and existing["cnt"] > 0:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany("""
            INSERT INTO questions (category,lang,q_type,question,option_a,option_b,option_c,answer,explanation,difficulty)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, SEED_QUESTIONS)
        await db.commit()
    log.info("✅ Seed questions inserted (Async).")
