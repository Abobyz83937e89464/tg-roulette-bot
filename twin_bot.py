from telethon import TelegramClient, events
import sqlite3
import asyncio

# === КОНФИГУРАЦИЯ ТВИНКА ===
API_ID = 29787074
API_HASH = 'b559ef4d37543417bdc4fb64fd50ff40'
PHONE = '+16363513308'  # ЗАМЕНИ НА НОМЕР ТВИНКА
PASSWORD = 'Пельмени'

# Разрешенные суммы пополнения
ALLOWED_AMOUNTS = [15, 25, 100]

# === БАЗА ДАННЫХ === 
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, stars INTEGER)''')
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

# === ОБРАБОТЧИКИ ТВИНКА ===
async def main():
    # Создаем клиент
    client = TelegramClient('twin_session', API_ID, API_HASH)
    
    @client.on(events.NewMessage(pattern='!пополнение (\d+)'))
    async def handle_deposit(event):
        """Обработка команды !пополнение"""
        try:
            amount = int(event.pattern_match.group(1))
            sender = await event.get_sender()
            
            if amount not in ALLOWED_AMOUNTS:
                await event.reply(
                    f"❌ Неверная сумма! Допустимые значения: {', '.join(map(str, ALLOWED_AMOUNTS))}"
                )
                return
            
            await event.reply(
                f"💫 Запрошено пополнение на {amount} звезд!\n\n"
                "🎁 **Оплачивайте подарок!**\n"
                "Киньте сердце ❤️ либо любой подарок нужной суммы!\n\n"
                "После отправки подарка звёзды будут автоматически начислены!"
            )
            print(f"💰 Запрос на пополнение: {amount} звезд от {sender.username}")
            
        except Exception as e:
            await event.reply("❌ Ошибка обработки запроса")
            print(f"Ошибка: {e}")
    
    @client.on(events.NewMessage)
    async def handle_gift(event):
        """Обработка подарков"""
        # Проверяем что это подарок (стикер или ключевые слова)
        is_gift = (
            event.message.sticker or 
            any(word in (event.message.text or '').lower() for word in ['сердце', 'подарок', 'gift', '❤️', '💝'])
        )
        
        if is_gift:
            # Ищем предыдущий запрос пополнения
            async for message in client.iter_messages(event.chat_id, limit=5):
                if message.text and '!пополнение' in message.text:
                    try:
                        amount = int(message.text.split()[1])
                        if amount in ALLOWED_AMOUNTS:
                            user_id = event.sender_id
                            current_user = get_user(user_id)
                            
                            if current_user:
                                new_balance = current_user[2] + amount
                                update_stars(user_id, new_balance)
                                
                                await event.reply(
                                    f"🎉 Платеж принят!\n"
                                    f"💫 На ваш баланс начислено: {amount} звезд\n"
                                    f"💰 Новый баланс: {new_balance} звезд\n\n"
                                    f"Возвращайтесь в бота: @YourBotName"
                                )
                                print(f"✅ Начислено {amount} звезд пользователю {user_id}")
                                
                            else:
                                await event.reply("❌ Пользователь не найден в системе")
                            
                            break
                    except Exception as e:
                        print(f"Ошибка начисления: {e}")
                    break
    
    # ЗАПУСК КЛИЕНТА
    print("🚀 Запускаю твинк...")
    await client.start(phone=PHONE, password=PASSWORD)
    print("✅ Твинк запущен! Ожидаю сообщения...")
    
    # Бесконечная работа
    await client.run_until_disconnected()

if __name__ == '__main__':
    init_db()
    asyncio.run(main())
