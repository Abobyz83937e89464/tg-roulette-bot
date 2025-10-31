from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import os
import time

BOT_TOKEN = os.getenv('BOT_TOKEN', '8052679500:AAEobQqpYnUxbfATmWa1tBIN-LZClPOUCbw')
WEB_APP_URL = "https://raw.githack.com/Abobyz83937e89464/tg-roulette-bot/main/web_app/index.html"

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, stars INTEGER, free_spin_time INTEGER)''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_stars(user_id, stars):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET stars=? WHERE user_id=?", (stars, user_id))
    conn.commit()
    conn.close()

def update_free_spin_time(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET free_spin_time=? WHERE user_id=?", (int(time.time()), user_id))
    conn.commit()
    conn.close()

def can_free_spin(user_id):
    user = get_user(user_id)
    if not user or user[3] == 0:
        return True, "00:00"
    else:
        time_passed = time.time() - user[3]
        if time_passed >= 86400:
            return True, "00:00"
        else:
            remaining = 86400 - time_passed
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            return False, f"{hours:02d}:{minutes:02d}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (user_id, username, stars, free_spin_time) VALUES (?, ?, ?, ?)", 
                 (user_id, update.effective_user.username, 50, 0))
        conn.commit()
        conn.close()
        user = (user_id, update.effective_user.username, 50, 0)
    
    can_spin, timer = can_free_spin(user_id)
    free_spin_text = "✨ Доступно сейчас!" if can_spin else f"⏰ Через: {timer}"
    
    keyboard = [
        [InlineKeyboardButton("🎮 ОТКРЫТЬ РУЛЕТКУ", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("💰 Мой баланс", callback_data="balance")],
        [InlineKeyboardButton("💫 Пополнить баланс", callback_data="deposit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎯 Добро пожаловать в Black Roulette!\n"
        f"💫 Ваш баланс: {user[2]} звезд\n"
        f"🎁 Бесплатная прокрутка: {free_spin_text}\n\n"
        "Нажмите кнопку ниже чтобы открыть рулетку:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if query.data == "balance":
        await query.answer(f"💫 Ваш баланс: {user[2]} звезд", show_alert=True)
    elif query.data == "deposit":
        await query.message.reply_text(
            "💫 ДЛЯ ПОПОЛНЕНИЯ БАЛАНСА:\n\n"
            "📝 Напишите боту @HE3BECTH0 по шаблону:\n\n"
            "!пополнение 15\n"
            "!пополнение 25\n" 
            "!пополнение 100\n\n"
            "🎁 После команды киньте любой подарок или стикер!\n\n"
            "✅ Звёзды начислятся автоматически!"
        )

if __name__ == '__main__':
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()
