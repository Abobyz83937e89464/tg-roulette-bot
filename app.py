from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import random
import os

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '8052679500:AAEobQqpYnUxbfATmWa1tBIN-LZClPOUCbw')
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://raw.githack.com/Abobyz83937e89464/tg-roulette-bot/main/web_app/index.html')

# Инициализация БД
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, stars INTEGER, spins INTEGER)''')
    conn.commit()
    conn.close()

def get_user(user_id, username=""):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    
    if not user:
        c.execute("INSERT INTO users (user_id, username, stars, spins) VALUES (?, ?, ?, ?)", 
                 (user_id, username, 10, 0))
        conn.commit()
        user = (user_id, username, 10, 0)
    
    conn.close()
    return user

def update_stars(user_id, stars):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET stars=? WHERE user_id=?", (stars, user_id))
    conn.commit()
    conn.close()

# Призы рулетки
ROULETTE_PRIZES = [
    {"name": "💫 5 звезд", "value": 5, "weight": 25},
    {"name": "✨ 10 звезд", "value": 10, "weight": 10},
    {"name": "⭐ 1 звезда", "value": 1, "weight": 40},
    {"name": "🎲 x2 множитель", "value": "multiplier", "weight": 15},
    {"name": "😞 Ничего", "value": 0, "weight": 10}
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user(user.id, user.username)
    
    keyboard = [
        [InlineKeyboardButton("🎰 Открыть рулетку", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton("💰 Мой баланс", callback_data="balance"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🔄 Крутить в чате", callback_data="spin_chat")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🎯 Добро пожаловать в Black Roulette, {user.first_name}!\n"
        f"💫 Ваш баланс: {user_data[2]} звезд\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    user_data = get_user(user.id, user.username)
    
    if query.data == "balance":
        await query.answer(f"💫 Ваш баланс: {user_data[2]} звезд", show_alert=True)
        
    elif query.data == "stats":
        await query.answer(f"📊 Статистика:\nВращений: {user_data[3]}\nБаланс: {user_data[2]} звезд", show_alert=True)
        
    elif query.data == "spin_chat":
        if user_data[2] < 1:
            await query.answer("❌ Недостаточно звезд для вращения!", show_alert=True)
            return
            
        # Логика спина
        total_weight = sum(prize["weight"] for prize in ROULETTE_PRIZES)
        random_value = random.randint(1, total_weight)
        current_weight = 0
        selected_prize = None
        
        for prize in ROULETTE_PRIZES:
            current_weight += prize["weight"]
            if random_value <= current_weight:
                selected_prize = prize
                break
        
        # Обновление баланса
        new_balance = user_data[2] - 1
        prize_value = selected_prize["value"]
        
        if prize_value == "multiplier":
            multiplier = random.randint(2, 5)
            win_amount = 1 * multiplier
            new_balance += win_amount
            result_text = f"🎲 Выпал множитель x{multiplier}! Вы выиграли {win_amount} звезд!"
        else:
            new_balance += prize_value
            result_text = f"🎯 Результат: {selected_prize['name']}!"
        
        update_stars(user.id, new_balance)
        
        # Обновление сообщения
        await query.edit_message_text(
            f"{result_text}\n"
            f"💫 Новый баланс: {new_balance} звезд\n\n"
            f"🎰 Хотите крутить еще?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Крутить еще", callback_data="spin_chat")],
                [InlineKeyboardButton("💰 Баланс", callback_data="balance")]
            ])
        )

if __name__ == '__main__':
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # ДЛЯ RAILWAY - используем polling
    application.run_polling()
