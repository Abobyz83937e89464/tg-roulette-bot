from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import os
import time

BOT_TOKEN = os.getenv('BOT_TOKEN', '8052679500:AAFxiWMPFBYzZBxpagvvZ_v0XYhHnf98EOW')

# Инициализация БД
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
    if not user or user[3] == 0:  # Первая бесплатная прокрутка
        return True, 0
    else:
        time_passed = time.time() - user[3]
        if time_passed >= 86400:  # 24 часа прошло
            return True, 0
        else:
            remaining = 86400 - time_passed
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            return False, f"{hours:02d}:{minutes:02d}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        # Создаем нового пользователя с балансом 50
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
        [InlineKeyboardButton("🎰 Крутить рулетку", callback_data="spin")],
        [InlineKeyboardButton("💰 Мой баланс", callback_data="balance")],
        [InlineKeyboardButton("💫 Пополнить баланс", callback_data="deposit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎯 Добро пожаловать в Black Roulette!\n"
        f"💫 Ваш баланс: {user[2]} звезд\n"
        f"🎁 Бесплатная прокрутка: {free_spin_text}\n\n"
        "Выберите действие:",
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
    elif query.data == "spin":
        can_spin, timer = can_free_spin(user_id)
        if can_spin:
            # Бесплатная прокрутка
            update_free_spin_time(user_id)
            await query.answer("🎰 Запускается бесплатная прокрутка!", show_alert=True)
        else:
            if user[2] >= 10:
                new_balance = user[2] - 10
                update_stars(user_id, new_balance)
                await query.answer("🎰 Запускается прокрутка за 10 звезд!", show_alert=True)
            else:
                await query.answer("❌ Недостаточно звезд для прокрутки!", show_alert=True)

if __name__ == '__main__':
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()
