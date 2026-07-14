import asyncio
import logging
import sqlite3
import os
import speech_recognition as sr
from datetime import timedelta
from pydub import AudioSegment
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
# === SOZLAMALAR ===
BOT_TOKEN = "8929855977:AAGq4CUWfC7fJm5FIWFliY5PZ6CD0iiBXh4"
ADMIN_ID = 8809803548  # O'zingizning Telegram ID raqamingizni yozing

# So'kinishlar bazasi (Shu yerga o'zingiz hamma so'zlarni kiritib chiqishingiz mumkin)
# Imloviy xatolarni payqash uchun o'zak so'zlarni yozish kifoya.
BAD_WORDS = [
    # O'zbek tilidagi so'zlar va ularning xato yozilishlari
    "jinni", "jini", "ahmoq", "axmoq", "yaramas", "iflos", "maraz", 
    "betayin", "chumo", "chmo", "lox", "qanjiq", "qanjik", "haromi", "xaromi",
    "kazzob", "padarkush", "jalab", "jallab", "foxisha", "fahiwa", "yiban", "qotoq", "iplos",
    "lux", "hezzim", "hezim", "hezalak","sikaman", "sikting","zb","am","skey","gandon"
    # Rus tilidagi so'zlar (keng tarqalgan o'zaklar va qisqartmalar)
    "durak", "dura", "debil", "idiot", "blya", "blyad", "suka", "syka", "cyka",
    "xuy", "hui", "xyi", "pizda", "pizdec", "ebat", "yoban", "gandon", "pidar", 
    "pidor", "shlyuxa", "shluxa", "zayeb", "zaeb",
    
    # Ingliz tilidagi so'zlar
    "fuck", "fck", "fuk", "shit", "bitch", "asshole", "dick", "cunt", 
    "bastard", "motherfucker", "slut", "whore", "dumbass", "pussy", "faggot"
]

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# === BAZA BILAN ISHLASH (SQLite) ===
def init_db():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS groups (group_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def add_group(group_id):
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO groups (group_id) VALUES (?)", (group_id,))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    users_count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    groups_count = c.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
    conn.close()
    return users_count, groups_count

def get_all_ids():
    conn = sqlite3.connect('bot_database.db')
    c = conn.cursor()
    users = [row[0] for row in c.execute("SELECT user_id FROM users").fetchall()]
    groups = [row[0] for row in c.execute("SELECT group_id FROM groups").fetchall()]
    conn.close()
    return users, groups

# === SO'KINISHNI TEKSHIRISH (Imloviy xatolar bilan) ===
def contains_bad_word(text: str) -> bool:
    text = text.lower().replace(" ", "").replace("_", "").replace("-", "")
    for word in BAD_WORDS:
        # Eng oddiy va tez ishlashi uchun so'z o'zagi qidiriladi
        if word.lower() in text:
            return True
    return False

# === START KOMANDASI ===
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Agar bot shaxsiy yozishmada (Lichkada) bo'lsa
    if message.chat.type == "private":
        add_user(message.from_user.id)
        
        # Guruhga qo'shish tugmasi
        bot_info = await bot.get_me()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Guruhga qo'shish", url=f"https://t.me/{bot_info.username}?startgroup=true")]
        ])
        
        await message.answer(
            "Salom! Men guruhlarni nazorat qiluvchi botman. Meni guruhingizga qo'shing va men xavfsizlikni ta'minlayman!",
            reply_markup=keyboard
        )
    else:
        # Agar guruhda start bosilsa
        add_group(message.chat.id)
        await message.answer("Bot ushbu guruhda muvaffaqiyatli ishga tushdi!")

# === ADMIN PANEL VA STATISTIKA ===
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    users, groups = get_stats()
    text = (
        f"👑 <b>Admin Panel</b>\n\n"
        f"👤 Jami foydalanuvchilar: {users}\n"
        f"👥 Jami guruhlar: {groups}\n\n"
        f"Reklama yuborish uchun quyidagi komandadan foydalaning:\n"
        f"<code>/reklama Sizning xabaringiz...</code>"
    )
    await message.answer(text)

# === REKLAMA TARQATISH TIZIMI ===
@dp.message(Command("reklama"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    ad_text = message.text.replace("/reklama", "", 1).strip()
    if not ad_text:
        await message.answer("Xabarni kiritmadingiz! Format: /reklama Xabar matni")
        return

    users, groups = get_all_ids()
    all_targets = users + groups
    success, fail = 0, 0

    await message.answer("Reklama tarqatish boshlandi...")

    for target_id in all_targets:
        try:
            await bot.send_message(chat_id=target_id, text=ad_text)
            success += 1
            await asyncio.sleep(0.05) # Telegram limitlariga tushib qolmaslik uchun
        except Exception:
            fail += 1

    await message.answer(f"✅ Reklama tarqatildi!\n\nMuvaffaqiyatli: {success}\nXatolik: {fail}")

# === JAZOLASH MANTIQI (1 DAQIQALIK BAN) ===
async def punish_user(message: types.Message):
    try:
        # Xabarni o'chirish
        await message.delete()
        
        # Ogohlantirish xabari
        warning = await message.answer(f"{message.from_user.first_name}, so'kinma yaramas! 1 daqiqaga bloklandingiz.")
        
        # 1 daqiqaga yozish huquqini olish (Mute/Ban)
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=message.date + timedelta(minutes=1)
        )
        
        # Ogohlantirishni 10 soniyadan keyin o'chirish (guruh toza turishi uchun)
        await asyncio.sleep(10)
        await warning.delete()
    except Exception as e:
        logging.error(f"Jazolashda xatolik: {e}")

# === MATNLI XABARLARNI TEKSHIRISH ===
@dp.message(F.text)
async def check_text(message: types.Message):
    # Guruhlarni bazaga qo'shib borish
    if message.chat.type in ["group", "supergroup"]:
        add_group(message.chat.id)

    if contains_bad_word(message.text):
        await punish_user(message)

# === OVOZLI XABARLARNI (VOICE) TEKSHIRISH ===
@dp.message(F.voice)
async def check_voice(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        add_group(message.chat.id)

    try:
        # 1. Ovozli xabarni yuklab olish
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        ogg_filename = f"voice_{message.from_user.id}.ogg"
        wav_filename = f"voice_{message.from_user.id}.wav"
        
        await bot.download_file(file_path, ogg_filename)
        
        # 2. OGG formatdan WAV formatga o'tkazish (ffmpeg kerak)
        audio = AudioSegment.from_ogg(ogg_filename)
        audio.export(wav_filename, format="wav")
        
        # 3. Ovozni matnga o'girish
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_filename) as source:
            audio_data = recognizer.record(source)
            # O'zbek tili uchun "uz-UZ", rus tili uchun "ru-RU"
            text = recognizer.recognize_google(audio_data, language="uz-UZ") 
            
        # 4. Matnni tekshirish
        if contains_bad_word(text):
            await punish_user(message)
            
    except sr.UnknownValueError:
        pass # Ovoz tushunarsiz bo'lsa e'tibor bermaslik
    except Exception as e:
        logging.error(f"Ovozni tekshirishda xatolik: {e}")
    finally:
        # Vaqtinchalik fayllarni tozalash
        if os.path.exists(ogg_filename): os.remove(ogg_filename)
        if os.path.exists(wav_filename): os.remove(wav_filename)

# === BOTNI ISHGA TUSHIRISH ===
async def main():
    init_db()
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())