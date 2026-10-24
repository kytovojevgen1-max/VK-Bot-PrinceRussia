import os
import json
import time
import random
from threading import Thread
from flask import Flask
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, EMPTY_KEYBOARD

# =====================================================================
# 1. ВЕБ-СЕРВЕР ДЛЯ RENDER (24/7 FREE)
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Prince Russia Ultimate Imba Core: ACTIVE 24/7"

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
if "promos" not in db: db["promos"] = {"PRINCE": 10000000, "RUSSIA": 5000000, "START": 25000000}
if "globals" not in db: db["globals"] = {"banned_users": []}
if "tickets" not in db: db["tickets"] = {}  # {target_id: {"question": "...", "status": "open", "answer": None, "admin": None}}

user_states = {}

RANKS = {
    0: "Игрок",
    1: "Медиа",
    2: "Модератор",
    3: "Администратор",
    4: "Спец. Администратор",
    5: "Главный Администратор",
    6: "Руководитель",
    7: "Главный Владелец"
}

def get_user_data(uid):
    uid_str = str(uid)
    if uid_str not in db["users"]:
        is_owner = 7 if int(uid) == MAIN_OWNER_ID else 0
        db["users"][uid_str] = {
            "money": 25000000,     # 25 млн руб бонус
            "bc": 1000,            # 1000 BC бонус
            "level": is_owner,
            "prefix": "[Основатель]" if is_owner else "[Игрок]",
            "username": f"id{uid}",
            "messages_count": 0,
            "activated_promos": [],
            "reg_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        if int(uid) == MAIN_OWNER_ID and db["users"][uid_str]["level"] < 7:
            db["users"][uid_str]["level"] = 7
            db["users"][uid_str]["prefix"] = "[Основатель]"
    return db["users"][uid_str]

async def resolve_user(identifier: str):
    """Ищет пользователя по ID или @username в базе"""
    clean_id = identifier.strip().replace("https://vk.com/", "").replace("vk.com/", "").replace("@", "").replace("id", "")
    if clean_id.isdigit():
        uid = int(clean_id)
        if str(uid) in db["users"]:
            return uid
    # Ищем по юзернейму
    search_str = identifier.strip().lower().replace("@", "")
    for u_str, u_info in db["users"].items():
        if u_info.get("username", "").lower().replace("@", "") == search_str:
            return int(u_str)
    return None


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
    keyboard.add(Text("📦 Контейнеры"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🎟 Промокод"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🆘 Техподдержка"), color=KeyboardButtonColor.NEGATIVE)
    if is_admin:
        keyboard.row()
        keyboard.add(Text("👑 Админ-Панель"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()

def get_admin_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("📢 Рассылка в ЛС"), color=KeyboardButtonColor.POSITIVE)
    keyboard.add(Text("💬 Рассылка по Беседам"), color=KeyboardButtonColor.POSITIVE)
    keyboard.row()
    keyboard.add(Text("📋 Список Тикетов"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("💬 Ответить на тикет"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("💰 Выдать Рубли"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("💎 Выдать BC"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("👑 Выдать Админку"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("🏷 Изменить Префикс"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🚫 Забанить"), color=KeyboardButtonColor.NEGATIVE)
    keyboard.add(Text("🟢 Разбанить"), color=KeyboardButtonColor.POSITIVE)
    keyboard.row()
    keyboard.add(Text("📊 Статистика Бота"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🔙 Главное меню"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()


# =====================================================================
# 4. ОБРАБОТКА ЛС И ИМБА-ФУНКЦИЙ
# =====================================================================

@bot.on.private_message(text=["/start", "Начать", "начать", "Меню", "меню", "Старт", "🔙 Главное меню", "❌ Отмена"])
async def start_handler(message: Message):
    uid = message.from_id
    if uid in db["globals"]["banned_users"]:
        return await message.answer("❌ Ваш аккаунт заблокирован в боте!")
        
    user_ids.add(uid)
    save_data(USERS_FILE, user_ids)
    u_data = get_user_data(uid)
    
    # Сохраняем актуальный юзернейм если есть в профиле ВК
    try:
        user_info = await bot.api.users.get(user_ids=[uid])
        if user_info and hasattr(user_info[0], "screen_name"):
            u_data["username"] = user_info[0].screen_name
    except Exception: pass
    
    save_data(DATA_DB_FILE, db)
    
    if uid in user_states: del user_states[uid]
    is_admin = u_data["level"] >= 3 or uid == MAIN_OWNER_ID
    
    welcome_text = (
        "👑 **PRINCE RUSSIA — MOBILE PROJECT** 👑\n"
        "*(Полная копия Black Russia)*\n"
        "───────────────────────────────\n"
        f"🏷 Префикс: **{u_data.get('prefix', '[Игрок]')}**\n"
        f"👤 Статус: **{RANKS.get(u_data['level'], 'Игрок')}**\n"
        f"💵 На руках: **{u_data['money']:,} руб.**\n"
        f"💎 BC Донат: **{u_data['bc']:,} BC**\n"
        "───────────────────────────────\n"
        "🔥 *Стартовый бонус: 25.000.000 руб. + 1000 BC!*"
    )
    await message.answer(welcome_text, keyboard=get_main_keyboard(is_admin))

@bot.on.private_message(text="👑 Админ-Панель")
async def admin_panel(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    await message.answer("🛠 **АДМИН-ПАНЕЛЬ PRINCE RUSSIA**\nВыберите действие с помощью кнопок ниже:", keyboard=get_admin_keyboard())

@bot.on.private_message(text=["📋 Профиль", "/profile"])
async def profile_handler(message: Message):
    uid = message.from_id
    u_data = get_user_data(uid)
    await message.answer(
        f"👤 **ВАШ ИГРОВОЙ ПРОФИЛЬ:**\n"
        f"───────────────\n"
        f"🆔 ID: `{uid}` | `@ {u_data.get('username', f'id{uid}')}`\n"
        f"🏷 Префикс: **{u_data.get('prefix', '[Игрок]')}**\n"
        f"👑 Ранг: **{RANKS.get(u_data['level'], 'Игрок')}**\n"
        f"💵 На руках: **{u_data['money']:,} руб.**\n"
        f"💎 BC Донат: **{u_data['bc']:,} BC**\n"
        f"✉️ Сообщений: `{u_data['messages_count']}`\n"
        f"📅 Регистрация: `{u_data['reg_date']}`"
    )

@bot.on.private_message(text=["🌐 Ссылки и Ресурсы", "Сайт"])
async def links_handler(message: Message):
    links_text = (
        "🌐 **ОФИЦИАЛЬНЫЕ РЕСУРСЫ PRINCE RUSSIA:**\n"
        "───────────────────────────────\n"
        "🌐 Сайт проекта: https://site-prince-russia.samp.date/\n"
        "📋 Форум: https://forum-prince-russia.samp.date/\n"
        "📢 ТГК проекта: https://t.me/prince_russiaa\n"
        "💬 ВКонтакте: https://vk.ru/princerussiaa\n"
        "🤖 Telegram-бот: https://t.me/PrinceRussiabot\n"
        "───────────────────────────────"
    )
    await message.answer(links_text)

@bot.on.private_message(text=["📦 Контейнеры", "/case"])
async def case_handler(message: Message):
    uid = message.from_id
    u_data = get_user_data(uid)
    cost = 250
    if u_data["bc"] < cost:
        return await message.answer(f"❌ Недостаточно BC доната! Открытие контейнера стоит **{cost} BC**.")
    u_data["bc"] -= cost
    win_money = random.randint(10000000, 100000000)
    u_data["money"] += win_money
    save_data(DATA_DB_FILE, db)
    await message.answer(f"📦 **ВЫ ОТКРЫЛИ КОНТЕЙНЕР ДУБАЙ!**\n🎉 Выигрыш: **+{win_money:,} рублей**!\n💎 Остаток: `{u_data['bc']:,} BC`")

@bot.on.private_message(text=["🎁 Бонус", "/bonus"])
async def bonus_handler(message: Message):
    uid = message.from_id
    u_data = get_user_data(uid)
    if time.time() - u_data.get("last_bonus", 0) < 86400:
        return await message.answer("⏳ Ежедневный бонус доступен ровно раз в 24 часа!")
    cash = 5000000
    u_data["money"] += cash
    u_data["last_bonus"] = time.time()
    save_data(DATA_DB_FILE, db)
    await message.answer(f"🎉 Вы успешно забрали ежедневный бонус и получили **+{cash:,} руб.**!")

@bot.on.private_message(text="🆘 Техподдержка")
async def support_prompt(message: Message):
    user_states[message.from_id] = "create_ticket"
    await message.answer("✍️ Опишите вашу проблему или вопрос одним сообщением. Администрация ответит вам в ближайшее время:")

@bot.on.private_message(text="📋 Список Тикетов")
async def list_tickets(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    if not db["tickets"]:
        return await message.answer("📂 Активных тикетов в поддержке нет.")
    
    t_msg = "📂 **СПИСОК ВСЕХ ТИКЕТОВ ПОДДЕРЖКИ:**\n───────────────────────────────\n"
    for t_id, t_data in db["tickets"].items():
        u_info = db["users"].get(str(t_id), {})
        u_name = f"@{u_info.get('username', f'id{t_id}')}" if u_info.get('username') else f"ID: {t_id}"
        status_icon = "🟢 Отвечен" if t_data["status"] == "answered" else "🔴 Ожидает"
        t_msg += f"• Игрок: **{u_name}** | {status_icon}\n  ❓ Вопрос: *{t_data['question']}*\n"
        if t_data["answer"]:
            t_msg += f"  💬 Ответ ({t_data.get('admin', 'Админ')}): *{t_data['answer']}*\n"
        t_msg += "───────────────────────────────\n"
    await message.answer(t_msg)

@bot.on.private_message(text="💬 Ответить на тикет")
async def ans_ticket_prompt(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "answer_ticket_input"
    await message.answer("✍️ Введите в формате:\n`@username_или_ID текст_ответа`\n(Пример: `@durov Привет, всё починили!`):")

@bot.on.private_message(text="📊 Статистика Бота")
async def stats_handler(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    await message.answer(f"📊 **СТАТИСТИКА ПРОЕКТА:**\n👤 Игроков: `{len(user_ids)}`\n💬 Чатов рассылки: `{len(chat_ids)}`\n📂 Активных тикетов: `{len(db['tickets'])}`")

@bot.on.private_message(text="📢 Рассылка в ЛС")
async def broadcast_pm(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "pm"
    await message.answer("✍️ Введите текст для рассылки **в ЛС игрокам**:")

@bot.on.private_message(text="💬 Рассылка по Беседам")
async def broadcast_chats(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "chats"
    await message.answer("✍️ Введите текст для рассылки **по всем беседам**:")

@bot.on.private_message(text="💰 Выдать Рубли")
async def give_money_prompt(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "give_money"
    await message.answer("✍️ Введите в формате: `@username_или_ID сумма`\n(Пример: `@durov 50000000`):")

@bot.on.private_message(text="💎 Выдать BC")
async def give_bc_prompt(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "give_bc"
    await message.answer("✍️ Введите в формате: `@username_или_ID сумма`\n(Пример: `@durov 1000`):")

@bot.on.private_message(text="👑 Выдать Админку")
async def give_admin_prompt(message: Message):
    if get_user_data(message.from_id)["level"] < 5: 
        return await message.answer("❌ Доступно только Главным Администраторам и Владельцу [5+]!")
    user_states[message.from_id] = "give_admin"
    await message.answer("✍️ Введите в формате: `@username_или_ID уровень(0-7)`\n(Пример: `@durov 3`):")

@bot.on.private_message(text="🏷 Изменить Префикс")
async def set_prefix_prompt(message: Message):
    if get_user_data(message.from_id)["level"] < 5: 
        return await message.answer("❌ Доступно только Главным Администраторам и Владельцу [5+]!")
    user_states[message.from_id] = "set_prefix"
    await message.answer("✍️ Введите в формате: `@username_или_ID [ВашПрефикс]`\n(Пример: `@durov [Куратор]`):")

@bot.on.private_message(text="🚫 Забанить")
async def ban_prompt(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "ban_user"
    await message.answer("✍️ Введите `@username` или `ID` игрока для блокировки:")

@bot.on.private_message(text="🟢 Разбанить")
async def unban_prompt(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "unban_user"
    await message.answer("✍️ Введите `@username` или `ID` игрока для разблокировки:")


# =====================================================================
# 5. ОБРАБОТКА ВВОДА И ТИКЕТОВ ПО ЮЗАМ И ID
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
    cmd = args[0].lower() if args else ""

    # Быстрый ответ командой /ans [юз/ID] [текст]
    if cmd in ["/ans", "/ответ", "ответ"] and len(args) >= 3:
        if u_data["level"] < 3: return
        target_uid = await resolve_user(args[1])
        if not target_uid:
            return await message.answer(f"❌ Пользователь `{args[1]}` не найден в базе!")
        reply_text = " ".join(args[2:])
        admin_prefix = u_data.get("prefix", "[Администратор]")
        admin_name = f"{admin_prefix} [id{uid}|Админ]"
        
        # Сохраняем в тикеты
        if str(target_uid) in db["tickets"]:
            db["tickets"][str(target_uid)]["status"] = "answered"
            db["tickets"][str(target_uid)]["answer"] = reply_text
            db["tickets"][str(target_uid)]["admin"] = admin_name
            save_data(DATA_DB_FILE, db)
            
        try:
            full_reply = (
                f"📩 **ОТВЕТ ОТ ТЕХПОДДЕРЖКИ PRINCE RUSSIA**\n"
                f"───────────────────────────────\n"
                f"👤 Администратор: **{admin_name}**\n"
                f"💬 Ответ: {reply_text}\n"
                f"───────────────────────────────"
            )
            await bot.api.messages.send(user_id=target_uid, message=full_reply, random_id=0)
            return await message.answer(f"✅ Ответ успешно отправлен игроку!")
        except Exception as e:
            return await message.answer(f"❌ Ошибка отправки: {e}")

    if uid in user_states:
        state = user_states[uid]
        del user_states[uid]
        
        if state == "create_ticket":
            db["tickets"][str(uid)] = {
                "question": text,
                "status": "open",
                "answer": None,
                "admin": None
            }
            save_data(DATA_DB_FILE, db)
            
            u_name = f"@{u_data.get('username', f'id{uid}')}"
            ticket_text = (
                f"🚨 **НОВЫЙ ТИКЕТ ПОДДЕРЖКИ**\n"
                f"👤 От: [id{uid}|Игрок] ({u_name})\n"
                f"💬 Текст: {text}\n\n"
                f"💡 *Для ответа введите:*\n`@ans {u_data.get('username', uid)} ваш_ответ`"
            )
            for u_str, u_info in db["users"].items():
                if u_info.get("level", 0) >= 3:
                    try:
                        await bot.api.messages.send(user_id=int(u_str), message=ticket_text, random_id=0)
                    except Exception: pass
            return await message.answer("✅ Ваше обращение отправлено в техподдержку! Администратор ответит вам в ЛС.")

        elif state == "answer_ticket_input":
            if len(args) < 2: return await message.answer("❌ Формат: `@юз_или_ID текст_ответа`")
            target_uid = await resolve_user(args[1])
            if not target_uid: return await message.answer(f"❌ Пользователь `{args[1]}` не найден!")
            reply_text = " ".join(args[2:])
            admin_name = f"{u_data.get('prefix', '[Админ]')} [id{uid}|Админ]"
            
            if str(target_uid) in db["tickets"]:
                db["tickets"][str(target_uid)]["status"] = "answered"
                db["tickets"][str(target_uid)]["answer"] = reply_text
                db["tickets"][str(target_uid)]["admin"] = admin_name
                save_data(DATA_DB_FILE, db)
                
            try:
                full_reply = (
                    f"📩 **ОТВЕТ ОТ ТЕХПОДДЕРЖКИ PRINCE RUSSIA**\n"
                    f"───────────────────────────────\n"
                    f"👤 Администратор: **{admin_name}**\n"
                    f"💬 Ответ: {reply_text}\n"
                    f"───────────────────────────────"
                )
                await bot.api.messages.send(user_id=target_uid, message=full_reply, random_id=0)
                return await message.answer("✅ Ответ успешно доставлен игроку!")
            except Exception as e:
                return await message.answer(f"❌ Ошибка: {e}")

        elif state == "pm":
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
            if len(args) < 2 or not args[1].isdigit():
                return await message.answer("❌ Формат: `@юз_или_ID сумма`")
            t_id = await resolve_user(args[0])
            if not t_id: return await message.answer(f"❌ Пользователь `{args[0]}` не найден!")
            amount = int(args[1])
            get_user_data(t_id)["money"] += amount
            save_data(DATA_DB_FILE, db)
            return await message.answer(f"✅ Игроку [id{t_id}|ID {t_id}] выдано `+{amount:,} руб.`.")

        elif state == "give_bc":
            if len(args) < 2 or not args[1].isdigit():
                return await message.answer("❌ Формат: `@юз_или_ID сумма`")
            t_id = await resolve_user(args[0])
            if not t_id: return await message.answer(f"❌ Пользователь `{args[0]}` не найден!")
            amount = int(args[1])
            get_user_data(t_id)["bc"] += amount
            save_data(DATA_DB_FILE, db)
            return await message.answer(f"✅ Игроку [id{t_id}|ID {t_id}] выдано `+{amount:,} BC`.")

        elif state == "give_admin":
            if len(args) < 2 or not args[1].isdigit():
                return await message.answer("❌ Формат: `@юз_или_ID уровень(0-7)`")
            t_id = await resolve_user(args[0])
            if not t_id: return await message.answer(f"❌ Пользователь `{args[0]}` не найден!")
            rank_lvl = int(args[1])
            if rank_lvl < 0 or rank_lvl > 7: return await message.answer("❌ Уровень от 0 до 7!")
            get_user_data(t_id)["level"] = rank_lvl
            save_data(DATA_DB_FILE, db)
            return await message.answer(f"✅ Игроку установлен ранг **{RANKS.get(rank_lvl, 'Игрок')}**.")

        elif state == "set_prefix":
            if len(args) < 2: return await message.answer("❌ Формат: `@юз_или_ID [Префикс]`")
            t_id = await resolve_user(args[0])
            if not t_id: return await message.answer(f"❌ Пользователь `{args[0]}` не найден!")
            new_prefix = " ".join(args[1:])
            get_user_data(t_id)["prefix"] = new_prefix
            save_data(DATA_DB_FILE, db)
            return await message.answer(f"✅ Установлен префикс: **{new_prefix}**.")

        elif state == "ban_user":
            t_id = await resolve_user(text)
            if not t_id: return await message.answer(f"❌ Пользователь `{text}` не найден!")
            if t_id not in db["globals"]["banned_users"]:
                db["globals"]["banned_users"].append(t_id)
                save_data(DATA_DB_FILE, db)
            return await message.answer(f"🚫 Пользователь [id{t_id}|ID {t_id}] заблокирован в боте.")

        elif state == "unban_user":
            t_id = await resolve_user(text)
            if not t_id: return await message.answer(f"❌ Пользователь `{text}` не найден!")
            if t_id in db["globals"]["banned_users"]:
                db["globals"]["banned_users"].remove(t_id)
                save_data(DATA_DB_FILE, db)
            return await message.answer(f"🟢 Пользователь [id{t_id}|ID {t_id}] разблокирован.")

        elif state == "activate_promo":
            code = text.strip().upper()
            if code not in db["promos"]: return await message.answer("❌ Промокод не найден!")
            if code in u_data["activated_promos"]: return await message.answer("❌ Вы уже активировали его!")
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
