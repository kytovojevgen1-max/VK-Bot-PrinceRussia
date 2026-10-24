import os
import json
import time
import random
from threading import Thread
from flask import Flask
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

# =====================================================================
# 1. ВЕБ-СЕРВЕР ДЛЯ RENDER (24/7 FREE)
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Prince Russia Official Bot Core: ACTIVE 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()


# =====================================================================
# 2. НАСТРОЙКИ И БАЗЫ ДАННЫХ
# =====================================================================
TOKEN = "vk1.a.msFlcd5y5n3ouSMUzsU5UYT2iSsz4oZpfqugFyFvBoDPuIJCuaTveRYFLZUWk7hLbnlLkLRivG5oRTMXhZU0SzOc1emMasJWDUD6NmWyEYjhc9uCa8dqbbTKb_EGadWM10CBTRPdvW-aeYAHS_sPp83X79GHyiDThjRh1qxRA_PdmEnk2mQGTYzf_gn8gby_7dwqLtrurXbwi2qw7w1kJw"
bot = Bot(token=TOKEN)

MAIN_OWNER_ID = 897082738  # Твой VK ID (Главный Владелец)

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"
DATA_DB_FILE = "data_db.json"

def load_data(filename, default_type=dict):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data) if default_type == set else data
        except Exception:
            return set() if default_type == set else {}
    return set() if default_type == set else {}

def save_data(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(list(data) if isinstance(data, set) else data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения {filename}: {e}")

user_ids = load_data(USERS_FILE, default_type=set)
chat_ids = load_data(CHATS_FILE, default_type=set)
db = load_data(DATA_DB_FILE, default_type=dict)

if "users" not in db: db["users"] = {}
if "promos" not in db: db["promos"] = {"PRINCE": 100000000, "RUSSIA": 50000000, "START": 25000000000}
if "globals" not in db: db["globals"] = {"banned_users": []}

user_states = {}

RANKS = {
    0: "Игрок",
    1: "Медиа",
    2: "Модератор",
    3: "Администратор",
    4: "Спец. Администратор",
    5: "Руководитель",
    7: "Главный Владелец"
}

def get_user_data(uid):
    uid_str = str(uid)
    if uid_str not in db["users"]:
        is_owner = 7 if int(uid) == MAIN_OWNER_ID else 0
        db["users"][uid_str] = {
            "money": 25000000000,  # 25 млрд рублей старт
            "donate": 1000,        # 1000 доната старт
            "level": is_owner,
            "messages_count": 0,
            "activated_promos": [],
            "reg_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        if int(uid) == MAIN_OWNER_ID and db["users"][uid_str]["level"] < 7:
            db["users"][uid_str]["level"] = 7
    return db["users"][uid_str]


# =====================================================================
# 3. КЛАВИАТУРЫ ДЛЯ ЛС
# =====================================================================

def get_main_keyboard(is_admin: bool):
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🚀 Начать играть"), color=KeyboardButtonColor.POSITIVE)
    keyboard.add(Text("🎁 Бонус"), color=KeyboardButtonColor.POSITIVE)
    keyboard.row()
    keyboard.add(Text("📋 Профиль"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("🌐 Ссылки и Ресурсы"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🎟 Промокод"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("📜 Команды"), color=KeyboardButtonColor.SECONDARY)
    if is_admin:
        keyboard.row()
        keyboard.add(Text("👑 Админ-Панель"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()

def get_admin_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("📢 Рассылка в ЛС"), color=KeyboardButtonColor.POSITIVE)
    keyboard.add(Text("💬 Рассылка по Беседам"), color=KeyboardButtonColor.POSITIVE)
    keyboard.row()
    keyboard.add(Text("📊 Статистика Бота"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("💰 Выдать Рубли"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("💎 Выдать Донат"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🔙 Главное меню"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()


# =====================================================================
# 4. ОБРАБОТКА ЛС И ИМБА-КОМАНД
# =====================================================================

@bot.on.private_message(text=["/start", "Начать", "начать", "Меню", "меню", "Старт", "🔙 Главное меню", "❌ Отмена"])
async def start_handler(message: Message):
    uid = message.from_id
    if uid in db["globals"]["banned_users"]:
        return await message.answer("❌ Ваш аккаунт заблокирован в боте!")
        
    user_ids.add(uid)
    save_data(USERS_FILE, user_ids)
    u_data = get_user_data(uid)
    save_data(DATA_DB_FILE, db)
    
    if uid in user_states: del user_states[uid]
    is_admin = u_data["level"] >= 3 or uid == MAIN_OWNER_ID
    
    welcome_text = (
        "👑 **PRINCE RUSSIA — MOBILE PROJECT** 👑\n"
        "*(Полная копия Black Russia)*\n"
        "───────────────────────────────\n"
        f"👤 Статус: **{RANKS.get(u_data['level'], 'Игрок')}**\n"
        f"💵 На руках: **{u_data['money']:,} руб.**\n"
        f"💎 Донат: **{u_data['donate']:,} UC**\n"
        "───────────────────────────────\n"
        "💡 *Стартовый бонус активирован: 25.000.000.000 руб. + 1000 доната!*"
    )
    await message.answer(welcome_text, keyboard=get_main_keyboard(is_admin))

@bot.on.private_message(text="👑 Админ-Панель")
async def admin_panel(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    await message.answer("🛠 **АДМИН-ПАНЕЛЬ PRINCE RUSSIA**\nВыберите действие:", keyboard=get_admin_keyboard())

@bot.on.private_message(text=["📋 Профиль", "/profile"])
async def profile_handler(message: Message):
    uid = message.from_id
    u_data = get_user_data(uid)
    await message.answer(
        f"👤 **ВАШ ИГРОВОЙ ПРОФИЛЬ:**\n"
        f"───────────────\n"
        f"🆔 VK ID: `{uid}`\n"
        f"👑 Ранг: **{RANKS.get(u_data['level'], 'Игрок')}**\n"
        f"💵 На руках: **{u_data['money']:,} руб.**\n"
        f"💎 Донат: **{u_data['donate']:,} UC**\n"
        f"✉️ Сообщений: `{u_data['messages_count']}`\n"
        f"📅 Регистрация: `{u_data['reg_date']}`"
    )

@bot.on.private_message(text=["🌐 Ссылки и Ресурсы", "Сайт"])
async def links_handler(message: Message):
    links_text = (
        "🌐 **ОФИЦИАЛЬНЫЕ РЕСУРСЫ PRINCE RUSSIA:**\n"
        "───────────────────────────────\n"
        f"🌐 Сайт проекта: https://site-prince-russia.samp.date/\n"
        f"📋 Форум: https://forum-prince-russia.samp.date/\n"
        f"близко ТГК: https://t.me/prince_russiaa\n"
        f"💬 ВКонтакте: https://vk.ru/princerussiaa\n"
        "───────────────────────────────"
    )
    await message.answer(links_text)

@bot.on.private_message(text=["🎁 Бонус", "/bonus"])
async def bonus_handler(message: Message):
    uid = message.from_id
    u_data = get_user_data(uid)
    if time.time() - u_data.get("last_bonus", 0) < 86400:
        return await message.answer("⏳ Ежедневный бонус доступен ровно раз в 24 часа!")
    cash = 1000000000  # 1 млрд руб бонус
    u_data["money"] += cash
    u_data["last_bonus"] = time.time()
    save_data(DATA_DB_FILE, db)
    await message.answer(f"🎉 Вы успешно забрали ежедневный бонус и получили **+{cash:,} руб.**!")

@bot.on.private_message(text=["📜 Команды", "/help"])
async def help_handler(message: Message):
    help_text = (
        "⭐ **ИГРОВЫЕ КОМАНДЫ БОТА:** ⭐\n"
        "───────────────────────────────\n"
        "• `Профиль` — Ваш игровой аккаунт\n"
        "• `Бонус` — Ежедневная награда\n"
        "• `Ссылки и Ресурсы` — Сайт, форум, ТГК, ВК\n"
        "• `Промокод` — Активация бонусов\n"
        "• `Начать играть` — Как зайти на проект\n"
        "───────────────────────────────"
    )
    await message.answer(help_text)

@bot.on.private_message(text="🚀 Начать играть")
async def play_handler(message: Message):
    await message.answer(
        "🚀 **КАК НАЧАТЬ ИГРАТЬ НА PRINCE RUSSIA:**\n"
        "1. Перейдите на наш сайт: https://site-prince-russia.samp.date/\n"
        "2. Скачайте официальный лаунчер.\n"
        "3. Установите игру и залетайте на сервер!\n\n"
        "🔥 *Не забудьте забрать стартовые 25 млрд рублей и 1000 доната!*"
    )

@bot.on.private_message(text="🎟 Промокод")
async def promo_prompt(message: Message):
    user_states[message.from_id] = "activate_promo"
    await message.answer("✍️ Введите ваш промокод в чат:")

@bot.on.private_message(text="📊 Статистика Бота")
async def stats_handler(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    await message.answer(
        f"📊 **СТАТИСТИКА ПРОЕКТА:**\n"
        f"───────────────\n"
        f"👤 Игроков в базе ЛС: `{len(user_ids)}` чел.\n"
        f"💬 Бесед для рассылок: `{len(chat_ids)}` шт."
    )

@bot.on.private_message(text="📢 Рассылка в ЛС")
async def broadcast_pm(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "pm"
    await message.answer(f"✍️ Введите текст для рассылки **в ЛС игрокам** (База: {len(user_ids)} чел.):")

@bot.on.private_message(text="💬 Рассылка по Беседам")
async def broadcast_chats(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "chats"
    await message.answer(f"✍️ Введите текст для рассылки **по всем беседам** (Всего чатов: {len(chat_ids)}):")

@bot.on.private_message(text="💰 Выдать Рубли")
async def give_money_prompt(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "give_money"
    await message.answer("✍️ Введите в формате: `ID_игрока сумма`\n(Пример: `123456789 500000000`):")

@bot.on.private_message(text="💎 Выдать Донат")
async def give_donate_prompt(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "give_donate"
    await message.answer("✍️ Введите в формате: `ID_игрока сумма`\n(Пример: `123456789 5000`):")


# =====================================================================
# 5. ТЕКСТОВЫЕ КОМАНДЫ И ОБРАБОТКА ВВОДА
# =====================================================================

@bot.on.private_message()
async def private_input(message: Message):
    uid = message.from_id
    if uid in db["globals"]["banned_users"]: return
    
    user_ids.add(uid)
    save_data(USERS_FILE, user_ids)
    text = message.text
    if not text: return

    u_data = get_user_data(uid)
    u_data["messages_count"] += 1
    save_data(DATA_DB_FILE, db)

    args = text.split()

    if uid in user_states:
        state = user_states[uid]
        del user_states[uid]
        
        if state == "pm":
            count = 0
            for u in list(user_ids):
                try:
                    await bot.api.messages.send(user_id=u, message=text, random_id=0)
                    count += 1
                except Exception: pass
            return await message.answer(f"✅ Рассылка в ЛС завершена! Доставлено: `{count}` игрокам.")
            
        elif state == "chats":
            count = 0
            for c in list(chat_ids):
                try:
                    await bot.api.messages.send(peer_id=c, message=text, random_id=0)
                    count += 1
                except Exception: pass
            return await message.answer(f"✅ Рассылка по беседам завершена! Отправлено в `{count}` чатов.")
            
        elif state == "give_money":
            if len(args) < 2 or not args[0].isdigit() or not args[1].isdigit():
                return await message.answer("❌ Ошибка формата! Используйте: `ID сумма`")
            t_id, amount = int(args[0]), int(args[1])
            get_user_data(t_id)["money"] += amount
            save_data(DATA_DB_FILE, db)
            return await message.answer(f"✅ Игроку [id{t_id}|ID {t_id}] успешно выдано `+{amount:,} руб.`.")

        elif state == "give_donate":
            if len(args) < 2 or not args[0].isdigit() or not args[1].isdigit():
                return await message.answer("❌ Ошибка формата! Используйте: `ID сумма`")
            t_id, amount = int(args[0]), int(args[1])
            get_user_data(t_id)["donate"] += amount
            save_data(DATA_DB_FILE, db)
            return await message.answer(f"✅ Игроку [id{t_id}|ID {t_id}] успешно выдано `+{amount:,} доната`.")

        elif state == "activate_promo":
            code = text.strip().upper()
            if code not in db["promos"]: return await message.answer("❌ Промокод не найден или устарел!")
            if code in u_data["activated_promos"]: return await message.answer("❌ Вы уже активировали этот промокод!")
            reward = db["promos"][code]
            u_data["money"] += reward
            u_data["activated_promos"].append(code)
            save_data(DATA_DB_FILE, db)
            return await message.answer(f"🎉 Промокод **{code}** активирован! Получено: **+{reward:,} руб.**.")


# =====================================================================
# 6. БЕСШУМНЫЙ СБОР ЧАТОВ ДЛЯ РАССЫЛОК
# =====================================================================

@bot.on.chat_message()
async def silent_chat_tracker(message: Message):
    if message.peer_id not in chat_ids:
        chat_ids.add(message.peer_id)
        save_data(CHATS_FILE, chat_ids)


if __name__ == "__main__":
    bot.run_forever()
