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
    return "Prince Russia Ultimate Core v10.1: ACTIVE 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()


# =====================================================================
# 2. НАСТРОЙКИ И БАЗЫ ДАННЫХ
# =====================================================================
TOKEN = "vk1.a.msFlcd5y5n3ouSMUzsU5UYT2iSsz4oZpfqugFyFvBoDPuIJCuaTveRYFLZUWk7hLbnlLkLRivG5oRTMXhZU0SzOc1emMasJWDUD6NmWyEYjhc9uCa8dqbbTKb_EGadWM10CBTRPdvW-aeYAHS_sPp83X79GHyiDThjRh1qxRA_PdmEnk2mQGTYzf_gn8gby_7dwqLtrurXbwi2qw7w1kJw"
bot = Bot(token=TOKEN)

MAIN_OWNER_ID = 897082738  # Твой VK ID (Разработчик игры / 8 lvl)

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
if "tickets" not in db: db["tickets"] = {}

user_states = {}
temp_admin_data = {}

RANKS = {
    0: "Игрок",
    1: "Медиа",
    2: "Модератор",
    3: "Администратор",
    4: "Спец. Администратор",
    5: "Главный Администратор",
    6: "Руководитель",
    7: "Заместитель Разработчика",
    8: "Разработчик игры"
}

def get_user_data(uid):
    uid_str = str(uid)
    if uid_str not in db["users"]:
        is_dev = 8 if int(uid) == MAIN_OWNER_ID else 0
        db["users"][uid_str] = {
            "money": 0,
            "bc": 0,
            "level": is_dev,
            "prefix": "[Разработчик]" if is_dev else "[Игрок]",
            "username": f"id{uid}",
            "messages_count": 0,
            "activated_promos": [],
            "reg_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        if int(uid) == MAIN_OWNER_ID and db["users"][uid_str]["level"] < 8:
            db["users"][uid_str]["level"] = 8
            db["users"][uid_str]["prefix"] = "[Разработчик]"
    return db["users"][uid_str]

async def resolve_user(identifier: str):
    clean_id = identifier.strip().replace("https://vk.com/", "").replace("vk.com/", "").replace("@", "").replace("id", "")
    if clean_id.isdigit():
        uid = int(clean_id)
        get_user_data(uid)
        return uid
    
    search_str = identifier.strip().lower().replace("@", "")
    for u_str, u_info in db["users"].items():
        if u_info.get("username", "").lower().replace("@", "") == search_str:
            return int(u_str)
            
    try:
        user_info = await bot.api.users.get(user_ids=[search_str])
        if user_info:
            uid = user_info[0].id
            get_user_data(uid)
            return uid
    except Exception:
        pass
    return None


# =====================================================================
# 3. КЛАВИАТУРЫ ДЛЯ ЛС
# =====================================================================

def get_main_keyboard(is_admin: bool):
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🚀 Скачать игру (Сайт)"), color=KeyboardButtonColor.POSITIVE)
    keyboard.row()
    keyboard.add(Text("📋 Профиль"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("🌐 Ссылки и Ресурсы"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("📦 Контейнеры"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🎲 Кости Удачи"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🎟 Промокод"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("🆘 Техподдержка"), color=KeyboardButtonColor.NEGATIVE)
    if is_admin:
        keyboard.row()
        keyboard.add(Text("👑 Админ-Панель"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()

def get_admin_keyboard(user_level: int):
    keyboard = Keyboard(one_time=False, inline=False)
    if user_level >= 6:
        keyboard.add(Text("📢 Рассылка в ЛС"), color=KeyboardButtonColor.POSITIVE)
        keyboard.add(Text("💬 Рассылка по Беседам"), color=KeyboardButtonColor.POSITIVE)
        keyboard.row()
    keyboard.add(Text("📋 Список Тикетов"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("👥 Список Админов"), color=KeyboardButtonColor.PRIMARY)
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
    
    try:
        user_info = await bot.api.users.get(user_ids=[uid])
        if user_info and hasattr(user_info[0], "screen_name"):
            u_data["username"] = user_info[0].screen_name
    except Exception: pass
    
    save_data(DATA_DB_FILE, db)
    
    if uid in user_states: del user_states[uid]
    is_admin = u_data["level"] >= 3 or uid == MAIN_OWNER_ID
    
    welcome_text = (
        "👑 **PRINCE RUSSIA — MOBILE PROJECT v10.1** 👑\n"
        "*(Полная копия Black Russia)*\n"
        "───────────────────────────────\n"
        f"🏷 Префикс: **{u_data.get('prefix', '[Игрок]')}**\n"
        f"👤 Статус: **{RANKS.get(u_data['level'], 'Игрок')}**\n"
        f"💵 На руках: **{u_data['money']:,} руб.**\n"
        f"💎 BC Донат: **{u_data['bc']:,} BC**\n"
        "───────────────────────────────\n"
        "🔥 **Бонус 25.000.000 руб. + 1000 BC** ждет вас на нашем официальном сайте при скачивании игры!"
    )
    await message.answer(welcome_text, keyboard=get_main_keyboard(is_admin))

@bot.on.private_message(text="👑 Админ-Панель")
async def admin_panel(message: Message):
    u_data = get_user_data(message.from_id)
    if u_data["level"] < 3: return
    await message.answer("🛠 **АДМИН-ПАНЕЛЬ PRINCE RUSSIA**\nВыберите действие с помощью кнопок ниже:", keyboard=get_admin_keyboard(u_data["level"]))

@bot.on.private_message(text=["📋 Профиль", "/profile"])
async def profile_handler(message: Message):
    uid = message.from_id
    u_data = get_user_data(uid)
    await message.answer(
        f"👤 **ВАШ ИГРОВОЙ ПРОФИЛЬ:**\n"
        f"───────────────\n"
        f"🆔 ID: [id{uid}|`{uid}`] | [id{uid}|@ {u_data.get('username', f'id{uid}')}]\n"
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
        "🌐 Сайт (скачать игру + бонус 25кк + 1000 BC): https://site-prince-russia.samp.date/\n"
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

@bot.on.private_message(text=["🎲 Кости Удачи", "Кости"])
async def dice_handler(message: Message):
    uid = message.from_id
    u_data = get_user_data(uid)
    cost = 1000000
    if u_data["money"] < cost:
        return await message.answer(f"❌ Для игры в кости нужно минимум **{cost:,} руб.** на руках!")
    
    u_data["money"] -= cost
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    
    if player_roll > bot_roll:
        win = cost * 2
        u_data["money"] += win
        save_data(DATA_DB_FILE, db)
        await message.answer(f"🎲 **КОСТИ УДАЧИ:**\nВы выбросили: `{player_roll}` | Бот выбросил: `{bot_roll}`\n🎉 Поздравляем! Вы выиграли **+{win:,} руб.**!")
    elif player_roll == bot_roll:
        u_data["money"] += cost
        save_data(DATA_DB_FILE, db)
        await message.answer(f"🎲 **КОСТИ УДАЧИ:**\nНичья! `{player_roll} : {bot_roll}`. Ставка возвращена.")
    else:
        save_data(DATA_DB_FILE, db)
        await message.answer(f"🎲 **КОСТИ УДАЧИ:**\nВы выбросили: `{player_roll}` | Бот выбросил: `{bot_roll}`\n😢 К сожалению, вы проиграли ставку `{cost:,} руб.`.")

@bot.on.private_message(text="🆘 Техподдержка")
async def support_prompt(message: Message):
    user_states[message.from_id] = "create_ticket"
    await message.answer("✍️ Опишите вашу проблему или вопрос одним сообщением. Администрация ответит вам в ближайшее время:")

@bot.on.private_message(text="📋 Список Тикетов")
async def list_tickets(message: Message):
    u_data = get_user_data(message.from_id)
    if u_data["level"] < 3: return
    if not db["tickets"]:
        return await message.answer("📂 Активных тикетов в поддержке нет.")
    
    t_msg = "📂 **СПИСОК АКТИВНЫХ ТИКЕТОВ:**\n───────────────────────────────\n"
    for t_id, t_data in db["tickets"].items():
        u_info = db["users"].get(str(t_id), {})
        u_handle = f"@{u_info.get('username', f'id{t_id}')}" if u_info.get('username') else f"ID: {t_id}"
        t_msg += f"• Игрок: [id{t_id}|{u_handle}] ([id{t_id}|ID {t_id}])\n  ❓ Вопрос: *{t_data['question']}*\n───────────────────────────────\n"
    
    await message.answer(t_msg, keyboard=get_admin_keyboard(u_data["level"]))

@bot.on.private_message(text="👥 Список Админов")
async def list_admins(message: Message):
    u_data = get_user_data(message.from_id)
    if u_data["level"] < 3: return
    
    admins = []
    for u_str, u_info in db["users"].items():
        if u_info.get("level", 0) >= 1:
            admins.append((int(u_str), u_info))
            
    if not admins:
        return await message.answer("👥 Администраторов в базе пока нет.")
        
    admins.sort(key=lambda x: x[1].get("level", 0), reverse=True)
    
    adm_msg = "👑 **АКТУАЛЬНЫЙ СПИСОК АДМИНИСТРАЦИИ:**\n───────────────────────────────\n"
    for a_id, a_info in admins:
        lvl = a_info.get("level", 0)
        rank_name = RANKS.get(lvl, "Админ")
        pref = a_info.get("prefix", "[Админ]")
        u_handle = f"@{a_info.get('username', f'id{a_id}')}" if a_info.get('username') else f"ID: {a_id}"
        
        adm_msg += f"• [id{a_id}|{u_handle}] ([id{a_id}|ID {a_id}]) ➔ {pref} **{rank_name}** `[{lvl} lvl]`\n"
        
    adm_msg += "───────────────────────────────"
    await message.answer(adm_msg, keyboard=get_admin_keyboard(u_data["level"]))

@bot.on.private_message(text="📊 Статистика Бота")
async def stats_handler(message: Message):
    u_data = get_user_data(message.from_id)
    if u_data["level"] < 3: return
    await message.answer(f"📊 **СТАТИСТИКА ПРОЕКТА:**\n👤 Игроков: `{len(user_ids)}`\n💬 Чатов рассылки: `{len(chat_ids)}`\n📂 Активных тикетов: `{len(db['tickets'])}`")

# КНОПКИ РАССЫЛОК (ТОЛЬКО ДЛЯ 6+ ЛВЛ)
@bot.on.private_message(text="📢 Рассылка в ЛС")
async def broadcast_pm_btn(message: Message):
    u_data = get_user_data(message.from_id)
    if u_data["level"] < 6: return await message.answer("❌ Доступно только с 6 уровня (Руководитель и выше)!")
    user_states[message.from_id] = "broadcast_pm_text"
    await message.answer("📢 **РАССЫЛКА В ЛС ИГРОКАМ**\n\nВведите текст сообщения для рассылки всем пользователям:")

@bot.on.private_message(text="💬 Рассылка по Беседам")
async def broadcast_chats_btn(message: Message):
    u_data = get_user_data(message.from_id)
    if u_data["level"] < 6: return await message.answer("❌ Доступно только с 6 уровня (Руководитель и выше)!")
    user_states[message.from_id] = "broadcast_chats_text"
    await message.answer("💬 **РАССЫЛКА ПО БЕСЕДАМ**\n\nВведите текст сообщения для рассылки по всем беседам, где добавлен бот:")

# КНОПОЧНЫЕ ДЕЙСТВИЯ АДМИНОВ
@bot.on.private_message(text="💰 Выдать Рубли")
async def btn_give_money(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "step_money_user"
    await message.answer("💰 **ВЫДАЧА РУБЛЕЙ**\n\nШаг 1 из 2: Введите `@username`, ссылку или `ID` игрока:")

@bot.on.private_message(text="💎 Выдать BC")
async def btn_give_bc(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "step_bc_user"
    await message.answer("💎 **ВЫДАЧА BC ДОНАТА**\n\nШаг 1 из 2: Введите `@username`, ссылку или `ID` игрока:")

@bot.on.private_message(text="👑 Выдать Админку")
async def btn_give_admin(message: Message):
    if get_user_data(message.from_id)["level"] < 5: return await message.answer("❌ Доступно с 5 уровня!")
    user_states[message.from_id] = "step_admin_user"
    await message.answer("👑 **ВЫДАЧА АДМИНИСТРИРОВАНИЯ**\n\nШаг 1 из 2: Введите `@username`, ссылку или `ID` игрока:")

@bot.on.private_message(text="🏷 Изменить Префикс")
async def btn_set_prefix(message: Message):
    if get_user_data(message.from_id)["level"] < 5: return await message.answer("❌ Доступно с 5 уровня!")
    user_states[message.from_id] = "step_prefix_user"
    await message.answer("🏷 **СМЕНА ПРЕФИКСА**\n\nШаг 1 из 2: Введите `@username`, ссылку или `ID` игрока:")

@bot.on.private_message(text="🚫 Забанить")
async def btn_ban(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "step_ban_user"
    await message.answer("🚫 **БЛОКИРОВКА ИГРОКА**\n\nШаг 1 из 2: Введите `@username`, ссылку или `ID` нарушителя:")

@bot.on.private_message(text="🟢 Разбанить")
async def btn_unban(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "step_unban"
    await message.answer("🟢 **РАЗБЛОКИРОВКА ИГРОКА**\n\nВведите `@username`, ссылку или `ID` игрока для снятия бана:")

@bot.on.private_message(text="💬 Ответить на тикет")
async def btn_ans_ticket(message: Message):
    if get_user_data(message.from_id)["level"] < 3: return
    user_states[message.from_id] = "step_ans_user"
    await message.answer("💬 **ОТВЕТ НА ТИКЕТ ПОДДЕРЖКИ**\n\nШаг 1 из 2: Введите `@username`, ссылку или `ID` игрока, которому хотите ответить:")

@bot.on.private_message(text="🚀 Скачать игру (Сайт)")
async def download_game(message: Message):
    await message.answer(
        "🚀 **СКАЧАТЬ PRINCE RUSSIA (Black Russia Mobile):**\n"
        "───────────────────────────────\n"
        "👉 Перейдите на наш официальный сайт: https://site-prince-russia.samp.date/\n\n"
        "🔥 *Там вы сможете скачать лаунчер, установить игру и получить стартовые **25.000.000 рублей + 1000 BC** доната на свой игровой аккаунт!*"
    )


# =====================================================================
# 5. ТЕКСТОВЫЕ КОМАНДЫ И УМНЫЙ ПОШАГОВЫЙ ВВОД ДЛЯ АДМИНОВ
# =====================================================================

@bot.on.private_message()
async def private_input(message: Message):
    uid = message.from_id
    if uid in db["globals"]["banned_users"]: return
    
    user_ids.add(uid)
    save_data(USERS_FILE, user_ids)
    
    u_data = get_user_data(uid)
    
    if message.payload and u_data["level"] >= 3:
        try:
            payload_data = json.loads(message.payload) if isinstance(message.payload, str) else message.payload
            action = payload_data.get("action")
            target_uid = payload_data.get("uid")
            
            if action == "ans_ticket":
                temp_admin_data[uid] = {"target_uid": target_uid}
                user_states[uid] = "step_ans_text_only"
                u_handle = f"@{db['users'].get(str(target_uid), {}).get('username', f'id{target_uid}')}"
                return await message.answer(f"✍️ Введите текст ответа для игрока [id{target_uid}|{u_handle}] (ID: `{target_uid}`):")
            elif action == "close_ticket":
                if str(target_uid) in db["tickets"]:
                    del db["tickets"][str(target_uid)]
                    save_data(DATA_DB_FILE, db)
                    try:
                        await bot.api.messages.send(user_id=int(target_uid), message="❌ Ваш тикет в техподдержку был закрыт администратором без ответа.", random_id=0)
                    except Exception: pass
                return await message.answer(f"✅ Тикет игрока [id{target_uid}|ID {target_uid}] успешно закрыт.")
        except Exception: pass

    text = message.text
    if not text: return

    u_data["messages_count"] += 1
    save_data(DATA_DB_FILE, db)

    args = text.split()

    if uid in user_states:
        state = user_states[uid]
        
        # --- РАССЫЛКА В ЛС ---
        if state == "broadcast_pm_text":
            del user_states[uid]
            if u_data["level"] < 6: return await message.answer("❌ Недостаточно прав!")
            count = 0
            for u in list(user_ids):
                try:
                    await bot.api.messages.send(user_id=u, message=text, random_id=0)
                    count += 1
                except Exception: pass
            return await message.answer(f"✅ Рассылка в ЛС завершена! Успешно доставлено: `{count}` игрокам.", keyboard=get_admin_keyboard(u_data["level"]))

        # --- РАССЫЛКА ПО БЕСЕДАМ ---
        elif state == "broadcast_chats_text":
            del user_states[uid]
            if u_data["level"] < 6: return await message.answer("❌ Недостаточно прав!")
            count = 0
            for c in list(chat_ids):
                try:
                    await bot.api.messages.send(peer_id=c, message=text, random_id=0)
                    count += 1
                except Exception: pass
            return await message.answer(f"✅ Рассылка по беседам завершена! Отправлено в `{count}` чатов.", keyboard=get_admin_keyboard(u_data["level"]))

        # --- ПОШАГОВЫЙ ВВОД ДЛЯ ВЫДАЧИ РУБЛЕЙ ---
        elif state == "step_money_user":
            del user_states[uid]
            t_id = await resolve_user(text)
            if not t_id: return await message.answer("❌ Пользователь не найден!")
            temp_admin_data[uid] = {"target_uid": t_id}
            user_states[uid] = "step_money_amount"
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"Выбран игрок: [id{t_id}|{t_handle}] ([id{t_id}|ID {t_id}])\n\nШаг 2 из 2: Введите сумму рублей для выдачи (например: `50000000`):")
            
        elif state == "step_money_amount":
            del user_states[uid]
            if not text.isdigit(): return await message.answer("❌ Сумма должна быть числом!")
            amt = int(text)
            t_id = temp_admin_data.get(uid, {}).get("target_uid")
            get_user_data(t_id)["money"] += amt
            save_data(DATA_DB_FILE, db)
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"✅ Успешно выдано `+{amt:,} руб.` игроку [id{t_id}|{t_handle}] ([id{t_id}|ID {t_id}]).", keyboard=get_admin_keyboard(u_data["level"]))

        # --- ПОШАГОВЫЙ ВВОД ДЛЯ ВЫДАЧИ BC ---
        elif state == "step_bc_user":
            del user_states[uid]
            t_id = await resolve_user(text)
            if not t_id: return await message.answer("❌ Пользователь не найден!")
            temp_admin_data[uid] = {"target_uid": t_id}
            user_states[uid] = "step_bc_amount"
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"Выбран игрок: [id{t_id}|{t_handle}] ([id{t_id}|ID {t_id}])\n\nШаг 2 из 2: Введите сумму BC доната (например: `1000`):")
            
        elif state == "step_bc_amount":
            del user_states[uid]
            if not text.isdigit(): return await message.answer("❌ Сумма должна быть числом!")
            amt = int(text)
            t_id = temp_admin_data.get(uid, {}).get("target_uid")
            get_user_data(t_id)["bc"] += amt
            save_data(DATA_DB_FILE, db)
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"✅ Успешно выдано `+{amt:,} BC` игроку [id{t_id}|{t_handle}] ([id{t_id}|ID {t_id}]).", keyboard=get_admin_keyboard(u_data["level"]))

        # --- ПОШАГОВЫЙ ВВОД ДЛЯ ВЫДАЧИ АДМИНКИ ---
        elif state == "step_admin_user":
            del user_states[uid]
            t_id = await resolve_user(text)
            if not t_id: return await message.answer("❌ Пользователь не найден!")
            temp_admin_data[uid] = {"target_uid": t_id}
            user_states[uid] = "step_admin_lvl"
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"Выбран игрок: [id{t_id}|{t_handle}] ([id{t_id}|ID {t_id}])\n\nШаг 2 из 2: Введите уровень администратора от 0 до 8:")
            
        elif state == "step_admin_lvl":
            del user_states[uid]
            if not text.isdigit(): return await message.answer("❌ Уровень должен быть числом!")
            lvl = int(text)
            if lvl < 0 or lvl > 8: return await message.answer("❌ Уровень от 0 до 8!")
            t_id = temp_admin_data.get(uid, {}).get("target_uid")
            get_user_data(t_id)["level"] = lvl
            save_data(DATA_DB_FILE, db)
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"✅ Установлен ранг **{RANKS.get(lvl, 'Игрок')} [{lvl} lvl]** для игрока [id{t_id}|{t_handle}].", keyboard=get_admin_keyboard(u_data["level"]))

        # --- ПОШАГОВЫЙ ВВОД ДЛЯ СМЕНЫ ПРЕФИКСА ---
        elif state == "step_prefix_user":
            del user_states[uid]
            t_id = await resolve_user(text)
            if not t_id: return await message.answer("❌ Пользователь не найден!")
            temp_admin_data[uid] = {"target_uid": t_id}
            user_states[uid] = "step_prefix_text"
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"Выбран игрок: [id{t_id}|{t_handle}] ([id{t_id}|ID {t_id}])\n\nШаг 2 из 2: Введите новый префикс (например: `[Куратор]`):")
            
        elif state == "step_prefix_text":
            del user_states[uid]
            pref = text.strip()
            t_id = temp_admin_data.get(uid, {}).get("target_uid")
            get_user_data(t_id)["prefix"] = pref
            save_data(DATA_DB_FILE, db)
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"✅ Успешно установлен префикс **{pref}** для игрока [id{t_id}|{t_handle}].", keyboard=get_admin_keyboard(u_data["level"]))

        # --- ПОШАГОВЫЙ ВВОД ДЛЯ БАНА С ПРИЧИНОЙ ---
        elif state == "step_ban_user":
            del user_states[uid]
            t_id = await resolve_user(text)
            if not t_id: return await message.answer("❌ Пользователь не найден!")
            temp_admin_data[uid] = {"target_uid": t_id}
            user_states[uid] = "step_ban_reason"
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"Выбран нарушитель: [id{t_id}|{t_handle}] ([id{t_id}|ID {t_id}])\n\nШаг 2 из 2: Введите причину блокировки:")
            
        elif state == "step_ban_reason":
            del user_states[uid]
            reason = text.strip()
            t_id = temp_admin_data.get(uid, {}).get("target_uid")
            if t_id not in db["globals"]["banned_users"]:
                db["globals"]["banned_users"].append(t_id)
                save_data(DATA_DB_FILE, db)
            try:
                await bot.api.messages.send(user_id=t_id, message=f"🚫 Вы были заблокированы в официальном боте Prince Russia!\nПричина: {reason}", random_id=0)
            except Exception: pass
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"🚫 Пользователь [id{t_id}|{t_handle}] ([id{t_id}|ID {t_id}]) успешно заблокирован!\nПричина: {reason}", keyboard=get_admin_keyboard(u_data["level"]))

        # --- РАЗБАН ---
        elif state == "step_unban":
            del user_states[uid]
            t_id = await resolve_user(text)
            if not t_id: return await message.answer("❌ Пользователь не найден!")
            if t_id in db["globals"]["banned_users"]:
                db["globals"]["banned_users"].remove(t_id)
                save_data(DATA_DB_FILE, db)
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"🟢 Пользователь [id{t_id}|{t_handle}] ([id{t_id}|ID {t_id}]) успешно разблокирован!", keyboard=get_admin_keyboard(u_data["level"]))

        # --- ОТВЕТ НА ТИКЕТ ---
        elif state == "step_ans_user":
            del user_states[uid]
            t_id = await resolve_user(text)
            if not t_id: return await message.answer("❌ Пользователь не найден!")
            temp_admin_data[uid] = {"target_uid": t_id}
            user_states[uid] = "step_ans_text"
            t_handle = f"@{db['users'].get(str(t_id), {}).get('username', f'id{t_id}')}"
            return await message.answer(f"Выбран игрок: [id{t_id}|{t_handle}] ([id{t_id}|ID {t_id}])\n\nШаг 2 из 2: Введите текст ответа игроку:")

        elif state == "step_ans_text" or state == "step_ans_text_only":
            t_id = temp_admin_data.get(uid, {}).get("target_uid")
            del user_states[uid]
            if not t_id: return await message.answer("❌ Ошибка сессии тикета.")
            
            admin_name = f"{u_data.get('prefix', '[Админ]')} [id{uid}|Админ]"
            if str(t_id) in db["tickets"]:
                del db["tickets"][str(t_id)]
                save_data(DATA_DB_FILE, db)
            try:
                await bot.api.messages.send(user_id=t_id, message=f"📩 **ОТВЕТ ОТ ТЕХПОДДЕРЖКИ:**\n👤 Администратор: **{admin_name}**\n💬 Ответ: {text}", random_id=0)
                return await message.answer("✅ Ответ успешно доставлен игроку, тикет закрыт!", keyboard=get_admin_keyboard(u_data["level"]))
            except Exception as e: return await message.answer(f"❌ Ошибка отправки: {e}")

        elif state == "create_ticket":
            db["tickets"][str(uid)] = {"question": text}
            save_data(DATA_DB_FILE, db)
            
            u_name = f"@{u_data.get('username', f'id{uid}')}"
            ticket_text = f"🚨 **НОВЫЙ ТИКЕТ**\n👤 От: [id{uid}|Игрок] ([id{uid}|{u_name}])\n💬 Вопрос: {text}"
            
            from vkbottle import Keyboard
            ticket_kb = Keyboard(one_time=False, inline=True)
            ticket_kb.add(Text("💬 Ответить", payload={"action": "ans_ticket", "uid": uid}), color=KeyboardButtonColor.POSITIVE)
            ticket_kb.add(Text("❌ Отклонить", payload={"action": "close_ticket", "uid": uid}), color=KeyboardButtonColor.NEGATIVE)
            
            for u_str, u_info in db["users"].items():
                if u_info.get("level", 0) >= 3:
                    try:
                        await bot.api.messages.send(user_id=int(u_str), message=ticket_text, keyboard=ticket_kb.get_json(), random_id=0)
                    except Exception: pass
            return await message.answer("✅ Ваше обращение отправлено в техподдержку! Администратор ответит вам в ЛС.")

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
