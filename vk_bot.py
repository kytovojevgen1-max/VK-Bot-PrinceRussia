import os
import json
import time
import random
from threading import Thread
from flask import Flask
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

# --- 1. ВЕБ-СЕРВЕР ДЛЯ RENDER (БЕСПЛАТНЫЙ ТАРИФ $0/mo) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Prince Russia Ultimate Bot is Online 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()


# --- 2. НАСТРОЙКИ И БАЗА ДАННЫХ ---
TOKEN = "vk1.a.msFlcd5y5n3ouSMUzsU5UYT2iSsz4oZpfqugFyFvBoDPuIJCuaTveRYFLZUWk7hLbnlLkLRivG5oRTMXhZU0SzOc1emMasJWDUD6NmWyEYjhc9uCa8dqbbTKb_EGadWM10CBTRPdvW-aeYAHS_sPp83X79GHyiDThjRh1qxRA_PdmEnk2mQGTYzf_gn8gby_7dwqLtrurXbwi2qw7w1kJw"
bot = Bot(token=TOKEN)

ADMIN_IDS = {897082738}  # Твой VK ID

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"
BONUS_FILE = "bonuses.json"

def load_data(filename, is_dict=False):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if is_dict else set(data)
        except Exception:
            return {} if is_dict else set()
    return {} if is_dict else set()

def save_data(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(list(data) if isinstance(data, set) else data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения {filename}: {e}")

user_ids = load_data(USERS_FILE)
chat_ids = load_data(CHATS_FILE)
bonus_db = load_data(BONUS_FILE, is_dict=True)

user_states = {}

# Список запрещенных слов (Защита бесед)
BAD_WORDS = ["дискорд", "discord.gg", "http://", "https://", "t.me/", "vk.me/join"]
PROMOCODES = {
    "PRINCE2026": "🎉 Вы получили 50,000 Prince Coins на сервер!",
    "START": "🎁 Ваш бонус: Скидка 20% на Донат-Кейс!"
}


# --- 3. КЛАВИАТУРЫ ---

def get_main_keyboard(is_admin: bool):
    keyboard = Keyboard(one_time=False, inline=False)
    
    keyboard.add(Text("🚀 Как начать играть"), color=KeyboardButtonColor.POSITIVE)
    keyboard.add(Text("🎁 Ежедневный бонус"), color=KeyboardButtonColor.POSITIVE)
    keyboard.row()
    
    keyboard.add(Text("🎬 Заявка на Медиа"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("🛡 Заявка на Админку"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    
    keyboard.add(Text("🎟 Промокод"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🌐 Наш Сайт"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    
    keyboard.add(Text("📋 Правила & FAQ"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🆘 Поддержка"), color=KeyboardButtonColor.NEGATIVE)
    
    if is_admin:
        keyboard.row()
        keyboard.add(Text("👑 Админ-Панель"), color=KeyboardButtonColor.PRIMARY)
        
    return keyboard.get_json()

def get_admin_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    
    keyboard.add(Text("📢 Рассылка в ЛС"), color=KeyboardButtonColor.POSITIVE)
    keyboard.add(Text("💬 Рассылка по Беседам"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🔑 Выдать Админку"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🔙 Главное меню"), color=KeyboardButtonColor.NEGATIVE)
    
    return keyboard.get_json()

def get_cancel_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("❌ Отмена"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()


# --- 4. ОБРАБОТКА ЛИЧНЫХ СООБЩЕНИЙ ---

@bot.on.private_message(text=["/start", "Начать", "начать", "Меню", "меню", "Старт", "🔙 Главное меню", "❌ Отмена"])
async def start_handler(message: Message):
    uid = message.from_id
    user_ids.add(uid)
    save_data(USERS_FILE, user_ids)
    
    if uid in user_states:
        del user_states[uid]
        
    is_admin = uid in ADMIN_IDS
    welcome_text = (
        "👑 **ДОБРО ПОЖАЛОВАТЬ В PRINCE RUSSIA OFFICIAL!** 👑\n\n"
        "Вы находитесь в главном меню официального бота проекта.\n"
        "Воспользуйтесь кнопками ниже для быстрой навигации:"
    )
    await message.answer(welcome_text, keyboard=get_main_keyboard(is_admin))

# --- АДМИН-ПАНЕЛЬ ---

@bot.on.private_message(text="👑 Админ-Панель")
async def admin_panel_handler(message: Message):
    if message.from_id not in ADMIN_IDS:
        return await message.answer("❌ У вас нет доступа к панели администратора.")
    
    admin_text = (
        "🛠 **АДМИН-ПАНЕЛЬ PRINCE RUSSIA**\n\n"
        f"📊 **Статистика:**\n"
        f"• Игроков в базе ЛС: `{len(user_ids)}` чел.\n"
        f"• Подключено бесед: `{len(chat_ids)}` чатов\n\n"
        "Выберите действие на клавиатуре ниже:"
    )
    await message.answer(admin_text, keyboard=get_admin_keyboard())

@bot.on.private_message(text="📢 Рассылка в ЛС")
async def broadcast_pm_start(message: Message):
    if message.from_id not in ADMIN_IDS: return
    user_states[message.from_id] = "awaiting_pm_broadcast"
    await message.answer("✍️ Отправьте сообщение для **всех пользователей в ЛС**:", keyboard=get_cancel_keyboard())

@bot.on.private_message(text="💬 Рассылка по Беседам")
async def broadcast_chats_start(message: Message):
    if message.from_id not in ADMIN_IDS: return
    user_states[message.from_id] = "awaiting_chats_broadcast"
    await message.answer("✍️ Отправьте новость для **всех бесед проекта**:", keyboard=get_cancel_keyboard())

@bot.on.private_message(text="🔑 Выдать Админку")
async def give_admin_start(message: Message):
    if message.from_id not in ADMIN_IDS: return
    user_states[message.from_id] = "awaiting_give_admin"
    await message.answer("✍️ Перешлите сообщение или укажите **VK ID** нового админа:", keyboard=get_cancel_keyboard())


# --- ОБРАБОТКА ВВОДА ЛС И КНОПОК ИГРОКОВ ---

@bot.on.private_message()
async def private_input_handler(message: Message):
    uid = message.from_id
    text = message.text
    
    # Режим ожидания ввода
    if uid in user_states:
        state = user_states[uid]
        
        if text.lower() == "❌ отмена":
            del user_states[uid]
            return await message.answer("❌ Отменено.", keyboard=get_main_keyboard(uid in ADMIN_IDS))
            
        if state == "awaiting_pm_broadcast" and uid in ADMIN_IDS:
            del user_states[uid]
            await message.answer("🚀 Запускаю рассылку в ЛС...")
            count = sum(1 for u in list(user_ids) if _send_safe(u, text))
            return await message.answer(f"✅ Доставлено `{count}` пользователям!", keyboard=get_admin_keyboard())

        elif state == "awaiting_chats_broadcast" and uid in ADMIN_IDS:
            del user_states[uid]
            await message.answer("🚀 Запускаю рассылку по беседам...")
            count = sum(1 for c in list(chat_ids) if _send_safe(c, text))
            return await message.answer(f"✅ Отправлено в `{count}` бесед(ы)!", keyboard=get_admin_keyboard())

        elif state == "awaiting_give_admin" and uid in ADMIN_IDS:
            del user_states[uid]
            target_id = message.reply_message.from_id if message.reply_message else (int(text) if text.isdigit() else None)
            if target_id:
                ADMIN_IDS.add(target_id)
                return await message.answer(f"🎉 Пользователь [id{target_id}|VK ID {target_id}] назначен админом бота!", keyboard=get_admin_keyboard())
            return await message.answer("❌ Ошибка ввода ID.", keyboard=get_admin_keyboard())

        elif state in ["awaiting_admin_app", "awaiting_media_app"]:
            app_type = "🛡 АДМИНКУ" if state == "awaiting_admin_app" else "🎬 МЕДИА"
            del user_states[uid]
            
            report = f"📥 **НОВАЯ ЗАЯВКА НА {app_type}!**\n\n👤 Игрок: [id{uid}|Ссылка]\n📝 АНКЕТА:\n{text}"
            for admin_id in ADMIN_IDS:
                _send_safe(admin_id, report)
            return await message.answer("✅ Ваша заявка успешно отправлена руководству! Ожидайте ответа.", keyboard=get_main_keyboard(uid in ADMIN_IDS))

        elif state == "awaiting_promo":
            del user_states[uid]
            code = text.upper().strip()
            if code in PROMOCODES:
                return await message.answer(f"✅ **ПРОМОКОД АКТИВИРОВАН!**\n\n{PROMOCODES[code]}", keyboard=get_main_keyboard(uid in ADMIN_IDS))
            return await message.answer("❌ Такого промокода не существует или он истёк!", keyboard=get_main_keyboard(uid in ADMIN_IDS))

    # Кнопки Главного Меню
    if text == "🚀 Как начать играть":
        msg = (
            "🚀 **КАК НАЧАТЬ ИГРАТЬ НА PRINCE RUSSIA?**\n\n"
            "1️⃣ Скачайте наш официальный лаунчер на сайте:\n"
            "👉 https://site-prince-russia.samp.date\n\n"
            "2️⃣ Установите APK и запустите игру!\n"
            "3️⃣ Выберите сервер **Prince Russia** и регистрируйте аккаунт!"
        )
        await message.answer(msg)

    elif text == "🎁 Ежедневный бонус":
        str_uid = str(uid)
        last_time = bonus_db.get(str_uid, 0)
        now = time.time()
        
        if now - last_time < 86400: # 24 часа
            hours = int((86400 - (now - last_time)) // 3600)
            return await message.answer(f"⏳ Вы уже забирали бонус! Следующая награда будет доступна через `{hours}` ч.")
            
        coins = random.randint(5000, 25000)
        bonus_db[str_uid] = now
        save_data(BONUS_FILE, bonus_db)
        await message.answer(f"🎉 **ЕЖЕДНЕВНЫЙ КЕЙС ОТКРЫТ!**\n\nВаш выигрыш: **+{coins:,} Prince Coins** 💰\nЗаходите завтра за новым бонусом!")

    elif text == "🎟 Промокод":
        user_states[uid] = "awaiting_promo"
        await message.answer("🎟 Введите действующий промокод в чат:", keyboard=get_cancel_keyboard())

    elif text == "🎬 Заявка на Медиа":
        user_states[uid] = "awaiting_media_app"
        await message.answer("🎥 **Заявка на Медиа-партнёрство**\n\nОтправьте ссылки на ваши каналы (YouTube/TikTok) и вашу статистику:", keyboard=get_cancel_keyboard())

    elif text == "🛡 Заявка на Админку":
        user_states[uid] = "awaiting_admin_app"
        form = "🛡 **Анкета на пост Администратора**\n\nУкажите одним сообщением:\n1. Ваш реальный возраст:\n2. Ваш игровой ник:\n3. Ваш часовой пояс:\n4. Опыт работы админом:"
        await message.answer(form, keyboard=get_cancel_keyboard())

    elif text == "🌐 Наш Сайт":
        await message.answer("🌐 Наш официальный сайт и UCP:\n👉 https://site-prince-russia.samp.date")

    elif text == "📋 Правила & FAQ":
        await message.answer("📜 Правила сервера и правила бесед доступны во вкладке «Статьи» нашей группы.")

    elif text == "🆘 Поддержка":
        await message.answer("🆘 Напишите вашу проблему, администрация ответит вам в ближайшее время!")

async def _send_safe(peer_id, text):
    try:
        await bot.api.messages.send(peer_id=peer_id, message=text, random_id=0)
        return True
    except Exception:
        return False


# --- 5. ОБРАБОТКА БЕСЕДИ & АНТИ-СПАМ ---

@bot.on.chat_message()
async def chat_handler(message: Message):
    if message.peer_id not in chat_ids:
        chat_ids.add(message.peer_id)
        save_data(CHATS_FILE, chat_ids)
        
    text = message.text.lower()
    
    # Фильтр рекламы и ссылок
    if any(bad in text for bad in BAD_WORDS):
        try:
            await bot.api.messages.delete(cmids=[message.conversation_message_id], peer_id=message.peer_id, delete_for_all=True)
            return await message.answer(f"⚠️ [id{message.from_id}|Пользователь], реклама и сторонние ссылки запрещены!")
        except Exception:
            pass

    # Команды модерации
    if text.startswith("!ник ") or text.startswith("/ник "):
        nick = message.text.split(" ", 1)[1] if " " in message.text else ""
        await message.answer(f"✅ Ваш ник изменен на: **{nick}**")
        
    elif text in ["!помощь", "/помощь"]:
        await message.answer("🛠 **Команды чат-менеджера:**\n• `!ник [текст]` — Установить кастомный ник\n• `!кик` — Исключить участника (ответом)\n• `!бан` — Забанить участника (ответом)")

if __name__ == "__main__":
    bot.run_forever()
