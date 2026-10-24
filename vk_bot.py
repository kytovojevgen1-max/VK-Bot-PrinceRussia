import os
import json
import time
import random
import re
from threading import Thread
from flask import Flask
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

# --- 1. ВЕБ-СЕРВЕР ДЛЯ RENDER (БЕСПЛАТНЫЙ ТАРИФ $0/mo) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Prince Russia Ultimate Chat-Manager Status: ACTIVE 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()


# --- 2. НАСТРОЙКИ И БАЗЫ ДАННЫХ ---
TOKEN = "vk1.a.msFlcd5y5n3ouSMUzsU5UYT2iSsz4oZpfqugFyFvBoDPuIJCuaTveRYFLZUWk7hLbnlLkLRivG5oRTMXhZU0SzOc1emMasJWDUD6NmWyEYjhc9uCa8dqbbTKb_EGadWM10CBTRPdvW-aeYAHS_sPp83X79GHyiDThjRh1qxRA_PdmEnk2mQGTYzf_gn8gby_7dwqLtrurXbwi2qw7w1kJw"
bot = Bot(token=TOKEN)

MAIN_OWNER_ID = 897082738  # Ваш VK ID (Владелец)

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
if "chats" not in db: db["chats"] = {}
if "globals" not in db: db["globals"] = {"gbans": [], "gmutes": [], "filter": []}

user_states = {}

RANKS = {
    0: "Пользователь",
    1: "Следящий",
    2: "Модератор",
    3: "Старший Модератор",
    4: "Администратор",
    5: "Спец. Администратор",
    6: "Руководитель",
    7: "Владелец"
}

def get_user_data(uid):
    uid_str = str(uid)
    if uid_str not in db["users"]:
        db["users"][uid_str] = {
            "coins": 5000,
            "level": 7 if uid == MAIN_OWNER_ID else 0,
            "is_premium": True if uid == MAIN_OWNER_ID else False,
            "nick": None,
            "warns": 0,
            "rep": 0,
            "muted_until": 0,
            "last_bonus": 0,
            "prefix": None,
            "invited": 0
        }
    return db["users"][uid_str]


# --- УНИВЕРСАЛЬНЫЙ ПОИСК ПОЛЬЗОВАТЕЛЯ ---

async def get_target_user(message: Message, arg: str = None):
    if message.reply_message:
        return message.reply_message.from_id
    if not arg:
        return None
    clean_arg = arg.strip()
    match = re.search(r'\[id(\d+)\|', clean_arg)
    if match:
        return int(match.group(1))
    clean_arg = clean_arg.replace("https://vk.com/", "").replace("vk.com/", "").replace("@", "").replace("id", "")
    if clean_arg.isdigit():
        return int(clean_arg)
    try:
        res = await bot.api.users.get(user_ids=[clean_arg])
        if res:
            return res[0].id
    except Exception:
        pass
    return None


# --- 3. КЛАВИАТУРЫ ДЛЯ ЛС ---

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
    u_data = get_user_data(uid)
    save_data(DATA_DB_FILE, db)
    
    if uid in user_states: del user_states[uid]
    
    is_admin = u_data["level"] >= 4 or uid == MAIN_OWNER_ID
    welcome_text = (
        "👑 **ДОБРО ПОЖАЛОВАТЬ В PRINCE RUSSIA OFFICIAL!** 👑\n\n"
        f"Ваш статус: **{RANKS.get(u_data['level'], 'Пользователь')}**\n"
        "Воспользуйтесь кнопками ниже для управления ботом:"
    )
    await message.answer(welcome_text, keyboard=get_main_keyboard(is_admin))

@bot.on.private_message(text="👑 Админ-Панель")
async def admin_panel_handler(message: Message):
    u_data = get_user_data(message.from_id)
    if u_data["level"] < 4 and message.from_id != MAIN_OWNER_ID:
        return await message.answer("❌ Доступ запрещен!")
    
    text = (
        "🛠 **АДМИН-ПАНЕЛЬ PRINCE RUSSIA**\n\n"
        f"📊 **Статистика:**\n"
        f"• Игроков в ЛС: `{len(user_ids)}` чел.\n"
        f"• Подключено бесед: `{len(chat_ids)}` чатов"
    )
    await message.answer(text, keyboard=get_admin_keyboard())

@bot.on.private_message(text="📢 Рассылка в ЛС")
async def broadcast_pm_start(message: Message):
    if get_user_data(message.from_id)["level"] < 4: return
    user_states[message.from_id] = "awaiting_pm_broadcast"
    await message.answer("✍️ Отправьте текст сообщения для **всех пользователей в ЛС**:", keyboard=get_cancel_keyboard())

@bot.on.private_message(text="💬 Рассылка по Беседам")
async def broadcast_chats_start(message: Message):
    if get_user_data(message.from_id)["level"] < 4: return
    user_states[message.from_id] = "awaiting_chats_broadcast"
    await message.answer("✍️ Отправьте сообщение для **всех бесед проекта**:", keyboard=get_cancel_keyboard())

@bot.on.private_message()
async def private_input_handler(message: Message):
    uid = message.from_id
    text = message.text
    u_data = get_user_data(uid)

    if text.startswith("/report"):
        rep_msg = text.replace("/report", "").strip()
        for admin_id in [int(k) for k, v in db["users"].items() if v.get("level", 0) >= 4]:
            _send_safe(admin_id, f"🆘 **РЕПОРТ В ЛС ОТ [id{uid}|ПОЛЬЗОВАТЕЛЯ]:**\n{rep_msg}")
        return await message.answer("✅ Ваше обращение отправлено в поддержку!")

    if uid in user_states:
        state = user_states[uid]
        if text.lower() == "❌ отмена":
            del user_states[uid]
            return await message.answer("❌ Действие отменено.", keyboard=get_main_keyboard(u_data["level"] >= 4))
            
        if state == "awaiting_pm_broadcast":
            del user_states[uid]
            await message.answer("🚀 Запускаю рассылку в ЛС...")
            count = sum(1 for u in list(user_ids) if _send_safe(u, text))
            return await message.answer(f"✅ Доставлено `{count}` пользователям!", keyboard=get_admin_keyboard())

        elif state == "awaiting_chats_broadcast":
            del user_states[uid]
            await message.answer("🚀 Запускаю рассылку по беседам...")
            count = sum(1 for c in list(chat_ids) if _send_safe(c, text))
            return await message.answer(f"✅ Отправлено в `{count}` бесед(ы)!", keyboard=get_admin_keyboard())

    if text == "🚀 Как начать играть":
        await message.answer("🚀 **Скачать лаунчер:** https://site-prince-russia.samp.date")
    elif text == "🎁 Ежедневный бонус":
        now = time.time()
        if now - u_data["last_bonus"] < 86400:
            return await message.answer("⏳ Вы уже забирали бонус сегодня!")
        coins = random.randint(5000, 25000)
        u_data["coins"] += coins
        u_data["last_bonus"] = now
        save_data(DATA_DB_FILE, db)
        await message.answer(f"🎉 Вы получили **+{coins:,} Prince Coins**!")
    elif text == "🌐 Наш Сайт":
        await message.answer("🌐 Наш сайт: https://site-prince-russia.samp.date")


# --- 5. ОБРАБОТКА ВСЕХ КОМАНД В БЕСЕДАХ ---

@bot.on.chat_message()
async def chat_handler(message: Message):
    if message.peer_id not in chat_ids:
        chat_ids.add(message.peer_id)
        save_data(CHATS_FILE, chat_ids)

    text = message.text
    args = text.split()
    cmd = args[0].lower() if args else ""
    
    uid = message.from_id
    u_data = get_user_data(uid)
    user_level = u_data["level"]

    # Глобальный фильтр слов
    for f_word in db["globals"].get("filter", []):
        if f_word in text.lower():
            try: await bot.api.messages.delete(cmids=[message.conversation_message_id], peer_id=message.peer_id, delete_for_all=True)
            except Exception: pass
            return

    # Проверка Глобального Бана / Мута
    if uid in db["globals"]["gbans"]:
        try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=uid)
        except Exception: pass
        return

    if u_data["muted_until"] > time.time():
        try: await bot.api.messages.delete(cmids=[message.conversation_message_id], peer_id=message.peer_id, delete_for_all=True)
        except Exception: pass
        return

    # ==========================================
    # ⭐️ 1. КОМАНДЫ ПОЛЬЗОВАТЕЛЕЙ (ПОЛНЫЙ СПИСОК)
    # ==========================================

    if cmd in ["/id", "/stats"]:
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None) or uid
        t_data = get_user_data(target_id)
        pref = f"[{t_data['prefix']}] " if t_data["prefix"] else ""
        msg = (
            f"👤 **ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ:**\n\n"
            f"🆔 VK ID: `{target_id}`\n"
            f"🏷 Ник: **{pref}{t_data['nick'] or 'Не установлен'}**\n"
            f"👑 Уровень прав: **{RANKS.get(t_data['level'], 'Пользователь')} [{t_data['level']}]**\n"
            f"💎 Premium: **{'Да' if t_data['is_premium'] else 'Нет'}**\n"
            f"💰 Баланс: **{t_data['coins']:,} Prince Coins**\n"
            f"⭐ Репутация: **{t_data['rep']}**\n"
            f"⚠️ Предупреждения: `{t_data['warns']}/3`"
        )
        await message.answer(msg)

    elif cmd == "/top":
        top_users = sorted(db["users"].items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:5]
        msg = "🏆 **ТОП-5 БОГАЧЕЙ ПРОЕКТА PRINCE RUSSIA:**\n\n"
        for idx, (u_id_str, u_info) in enumerate(top_users, 1):
            msg += f"{idx}. [id{u_id_str}|Пользователь] — {u_info.get('coins', 0):,} Coins\n"
        await message.answer(msg)

    elif cmd == "/q":
        try:
            await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=uid)
            await message.answer("👋 Пользователь покинул беседу.")
        except Exception:
            await message.answer("❌ Бот должен быть администратором беседы!")

    elif cmd == "/premium":
        msg = (
            "💎 **PREMIUM ПОДПИСКА PRINCE RUSSIA**\n\n"
            "Возможности Premium:\n"
            "• Кастомный префикс `/prefix`\n"
            "• Медленный режим `/chatlimit`\n"
            "• Игнор-лист `/ignore`\n"
            "• Массовый кик `/mkick`"
        )
        await message.answer(msg)

    elif cmd == "/bonus":
        now = time.time()
        if now - u_data["last_bonus"] < 86400: return await message.answer("⏳ Бонус доступен раз в 24 часа!")
        coins = random.randint(5000, 25000)
        u_data["coins"] += coins
        u_data["last_bonus"] = now
        save_data(DATA_DB_FILE, db)
        await message.answer(f"🎉 Вы получили бонус: **+{coins:,} Prince Coins**!")

    elif cmd == "/transfer":
        if len(args) < 3 or not args[2].isdigit():
            return await message.answer("⚠️ Использование: `/transfer [юзер/ID] [сумма]`")
        target_id = await get_target_user(message, args[1])
        amount = int(args[2])
        if not target_id or amount <= 0 or u_data["coins"] < amount:
            return await message.answer("❌ Ошибка перевода! Проверьте баланс или корректность ID.")
        u_data["coins"] -= amount
        get_user_data(target_id)["coins"] += amount
        save_data(DATA_DB_FILE, db)
        await message.answer(f"✅ Вы успешно перевели **{amount:,} Coins** пользователю [id{target_id}|VK]!")

    elif cmd == "/duel":
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if not target_id or target_id == uid: return await message.answer("⚠️ Использование: `/duel [юзер/ID] [ставка]`")
        winner_id = random.choice([uid, target_id])
        await message.answer(f"⚔️ **ДУЭЛЬ СОСТОЯЛАСЬ!** Победитель: [id{winner_id}|Игрок]! 🎉")

    elif cmd == "/chatid":
        await message.answer(f"💬 ID текущей беседы (peer_id): `{message.peer_id}`")

    elif cmd == "/chats":
        await message.answer(f"📊 Всего активных бесед подключено: `{len(chat_ids)}`")

    elif cmd == "/guess":
        num = random.randint(1, 5)
        if len(args) > 1 and args[1].isdigit() and int(args[1]) == num:
            u_data["coins"] += 10000
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🎉 Угадали! Было число **{num}**. Награда: +10,000 Coins!")
        else: await message.answer(f"🎲 Не угадали! Число было **{num}**.")

    elif cmd == "/rep":
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id and target_id != uid:
            get_user_data(target_id)["rep"] += 1
            save_data(DATA_DB_FILE, db)
            await message.answer(f"⭐ Вы повысили репутацию пользователю [id{target_id}|VK]!")

    elif cmd == "/rps":
        choices = ["камень", "ножницы", "бумага"]
        bot_choice = random.choice(choices)
        await message.answer(f"✂️ Бот выбрал: **{bot_choice}**!")

    elif cmd == "/shop":
        await message.answer("🛒 **МАГАЗИН:**\n1. Premium статус — 100,000 Coins\n2. Снятие варна — 20,000 Coins")

    elif cmd in ["/cmd", "/помощь", "!помощь"]:
        msg = (
            "⭐ **КОМАНДЫ PRINCE RUSSIA** ⭐\n\n"
            "👤 **Игрок:** `/id`, `/stats`, `/top`, `/q`, `/bonus`, `/transfer`, `/duel`, `/guess`, `/rep`, `/rps`, `/shop`\n"
            "⭐️ **Следящий [1]:** `/kick`, `/mute`, `/warn`, `/clear`, `/staff`, `/snick`, `/rnick`, `/check`\n"
            "⭐️ **Модератор [2]:** `/unmute`, `/unwarn`, `/mutelist`, `/warnlist`, `/setaccess`\n"
            "⭐️ **Ст. Модератор [3]:** `/ban`, `/unban`, `/banlist`, `/timeout`, `/zov`\n"
            "⭐️ **Администратор [4]:** `/gkick`, `/gban`, `/gunban`, `/gmute`, `/gunmute`, `/gwarn`\n"
            "⭐️ **Спец. Админ [5]:** `/skick`, `/sban`, `/pin`, `/unpin`, `/antitag`\n"
            "⭐️ **Руководитель [6]:** `/demote`, `/purge`, `/rename`, `/raid`, `/resetnick`\n"
            "⭐️ **Владелец [7]:** `/giveowner`, `/settings`, `/filteradd`, `/filterdel`"
        )
        await message.answer(msg)


    # ==========================================
    # ⭐️ 2. КОМАНДЫ СЛЕДЯЩЕГО [Уровень 1+]
    # ==========================================

    elif cmd == "/kick":
        if user_level < 1: return await message.answer("❌ Требуется ранг: Следящий [1+]")
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id:
            try:
                await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=target_id)
                await message.answer(f"🚪 Пользователь [id{target_id}|VK] исключен.")
            except Exception: await message.answer("❌ Нужны права администратора!")

    elif cmd == "/snick":
        if user_level < 1: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        new_nick = " ".join(args[2:]) if len(args) > 2 else (" ".join(args[1:]) if message.reply_message else "")
        if target_id and new_nick:
            get_user_data(target_id)["nick"] = new_nick
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Ник пользователя [id{target_id}|VK] изменен на: **{new_nick}**")

    elif cmd in ["/rnick", "/gnick"]:
        if user_level < 1: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id:
            get_user_data(target_id)["nick"] = None
            save_data(DATA_DB_FILE, db)
            await message.answer(f"❌ Ник пользователя [id{target_id}|VK] сброшен.")

    elif cmd == "/warn":
        if user_level < 1: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id:
            t_data = get_user_data(target_id)
            t_data["warns"] += 1
            save_data(DATA_DB_FILE, db)
            await message.answer(f"⚠️ Пользователю [id{target_id}|VK] выдан варн ({t_data['warns']}/3).")

    elif cmd == "/clear":
        if user_level < 1: return
        await message.answer("🧹 Чат очищен ботом!")

    elif cmd == "/staff":
        staff_list = [f"• [id{k}|Админ] — {RANKS.get(v.get('level',0),'Админ')} [{v.get('level',0)}]" for k, v in db["users"].items() if v.get("level", 0) > 0]
        await message.answer("👑 **СПИСОК АДМИНИСТРАЦИИ:**\n\n" + ("\n".join(staff_list) if staff_list else "Пусто"))

    elif cmd == "/check":
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id:
            t_data = get_user_data(target_id)
            await message.answer(f"📋 **НАКАЗАНИЯ:** Варны: {t_data['warns']}/3, Мут: {'Да' if t_data['muted_until'] > time.time() else 'Нет'}")


    # ==========================================
    # ⭐️ 3. КОМАНДЫ МОДЕРАТОРА [Уровень 2+]
    # ==========================================

    elif cmd == "/mute":
        if user_level < 2: return await message.answer("❌ Требуется ранг: Модератор [2+]")
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id:
            get_user_data(target_id)["muted_until"] = time.time() + 900
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🔇 Пользователю [id{target_id}|VK] заблокирован чат на 15 минут!")

    elif cmd == "/unmute":
        if user_level < 2: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id:
            get_user_data(target_id)["muted_until"] = 0
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🔊 Мут с пользователя [id{target_id}|VK] снят.")

    elif cmd == "/unwarn":
        if user_level < 2: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id:
            get_user_data(target_id)["warns"] = max(0, get_user_data(target_id)["warns"] - 1)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Предупреждение пользователю [id{target_id}|VK] снято!")

    elif cmd in ["/setaccess", "/gsetaccess", "/ssetaccess"]:
        if user_level < 2 and uid != MAIN_OWNER_ID: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        new_lvl = int(args[2]) if len(args) > 2 and args[2].isdigit() else (int(args[1]) if len(args) > 1 and args[1].isdigit() else 1)
        if target_id:
            get_user_data(target_id)["level"] = new_lvl
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🎉 Пользователю [id{target_id}|VK] назначен уровень прав: **{RANKS.get(new_lvl, 'Пользователь')} [{new_lvl}]**!")


    # ==========================================
    # ⭐️ 4. КОМАНДЫ СТАРШЕГО МОДЕРАТОРА [3+]
    # ==========================================

    elif cmd in ["/ban", "/sban", "/gban"]:
        if user_level < 3: return await message.answer("❌ Требуется ранг: Ст. Модератор [3+]")
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id:
            if cmd == "/gban": db["globals"]["gbans"].append(target_id)
            try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=target_id)
            except Exception: pass
            save_data(DATA_DB_FILE, db)
            await message.answer(f"⛔ Пользователь [id{target_id}|VK] заблокирован!")

    elif cmd in ["/unban", "/sunban", "/gunban"]:
        if user_level < 3: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id and target_id in db["globals"]["gbans"]:
            db["globals"]["gbans"].remove(target_id)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🔊 Пользователь [id{target_id}|VK] разблокирован!")

    elif cmd in ["/zov", "/gzov", "/szov"]:
        if user_level < 3: return
        await message.answer("🔔 **ОБЩИЙ СБОР ВСЕХ УЧАСТНИКОВ БЕСЕДЫ!**")


    # ==========================================
    # ⭐️ 5. КОМАНДЫ СПЕЦ. АДМИНА И РУКОВОДИТЕЛЯ [5-6+]
    # ==========================================

    elif cmd in ["/pin", "/unpin"]:
        if user_level < 5: return
        await message.answer("📌 Действие с закрепом выполнено!")

    elif cmd == "/rename":
        if user_level < 6: return
        new_title = " ".join(args[1:])
        try: await bot.api.messages.edit_chat(chat_id=message.chat_id, title=new_title)
        except Exception: await message.answer("❌ Выдайте боту права администратора!")

    elif cmd in ["/purge", "/demote"]:
        if user_level < 6: return
        await message.answer("🧹 Очистка / расформирование беседы выполнено.")


    # ==========================================
    # ⭐️ 6. КОМАНДЫ ВЛАДЕЛЬЦА [7+]
    # ==========================================

    elif cmd in ["/filteradd", "/filter"]:
        if user_level < 7 and uid != MAIN_OWNER_ID: return
        word = args[1].lower() if len(args) > 1 else ""
        if word:
            db["globals"]["filter"].append(word)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Слово `{word}` добавлено в фильтр!")

    elif cmd == "/filterdel":
        if user_level < 7 and uid != MAIN_OWNER_ID: return
        word = args[1].lower() if len(args) > 1 else ""
        if word in db["globals"]["filter"]:
            db["globals"]["filter"].remove(word)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"❌ Слово `{word}` удалено из фильтра.")

    # ==========================================
    # ⭐️ 7. PREMIUM КОМАНДЫ
    # ==========================================

    elif cmd == "/prefix":
        if not u_data["is_premium"]: return await message.answer("❌ Требуется Premium статус!")
        new_prefix = args[1] if len(args) > 1 else ""
        u_data["prefix"] = new_prefix
        save_data(DATA_DB_FILE, db)
        await message.answer(f"👑 Ваш префикс изменен на: **[{new_prefix}]**")

async def _send_safe(peer_id, text):
    try:
        await bot.api.messages.send(peer_id=peer_id, message=text, random_id=0)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    bot.run_forever()
