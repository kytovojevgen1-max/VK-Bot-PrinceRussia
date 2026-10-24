import os
import json
import time
import random
import re
from threading import Thread
from flask import Flask
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

# --- 1. ВЕБ-СЕРВЕР ДЛЯ RENDER (FREE $0/mo) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Prince Russia Ultimate Bot: ACTIVE 24/7"

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
if "globals" not in db: db["globals"] = {"gbans": [], "gmutes": [], "filter": ["дискорд", "discord.gg", "t.me/"]}

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
            "coins": 10000,
            "level": 7 if uid == MAIN_OWNER_ID else 0,
            "is_premium": True if uid == MAIN_OWNER_ID else False,
            "nick": None,
            "warns": 0,
            "rep": 0,
            "muted_until": 0,
            "last_bonus": 0,
            "prefix": None
        }
    return db["users"][uid_str]


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
    
    # СОХРАНЯЕМ В ЛС БАЗУ
    user_ids.add(uid)
    save_data(USERS_FILE, user_ids)
    u_data = get_user_data(uid)
    save_data(DATA_DB_FILE, db)
    
    if uid in user_states: del user_states[uid]
    
    is_admin = u_data["level"] >= 4 or uid == MAIN_OWNER_ID
    welcome_text = (
        "👑 **ДОБРО ПОЖАЛОВАТЬ В PRINCE RUSSIA OFFICIAL!** 👑\n"
        "───────────────────────────────\n"
        f"👤 Ваш статус: **{RANKS.get(u_data['level'], 'Пользователь')}**\n"
        f"💰 Баланс: **{u_data['coins']:,} Prince Coins**\n"
        "───────────────────────────────\n"
        "Воспользуйтесь кнопками ниже для управления ботом:"
    )
    await message.answer(welcome_text, keyboard=get_main_keyboard(is_admin))

@bot.on.private_message(text="👑 Админ-Панель")
async def admin_panel_handler(message: Message):
    u_data = get_user_data(message.from_id)
    if u_data["level"] < 4 and message.from_id != MAIN_OWNER_ID:
        return await message.answer("❌ У вас нет доступа к админ-панели!")
    
    text = (
        "🛠 **АДМИН-ПАНЕЛЬ PRINCE RUSSIA**\n"
        "───────────────────────────────\n"
        f"📊 **Статистика системы:**\n"
        f"• Пользователей в ЛС (база): `{len(user_ids)}` чел.\n"
        f"• Активных бесед: `{len(chat_ids)}` чатов\n"
        "───────────────────────────────\n"
        "Выберите действие на клавиатуре ниже:"
    )
    await message.answer(text, keyboard=get_admin_keyboard())

# --- РАССЫЛКИ ---

@bot.on.private_message(text="📢 Рассылка в ЛС")
async def broadcast_pm_start(message: Message):
    if get_user_data(message.from_id)["level"] < 4: return
    user_states[message.from_id] = "awaiting_pm_broadcast"
    await message.answer(f"✍️ Отправьте текст сообщения для **всех пользователей в ЛС** (Всего в базе: {len(user_ids)} чел.):", keyboard=get_cancel_keyboard())

@bot.on.private_message(text="💬 Рассылка по Беседам")
async def broadcast_chats_start(message: Message):
    if get_user_data(message.from_id)["level"] < 4: return
    user_states[message.from_id] = "awaiting_chats_broadcast"
    await message.answer(f"✍️ Отправьте сообщение для **всех подключенных бесед** (Всего бесед: {len(chat_ids)}):", keyboard=get_cancel_keyboard())

@bot.on.private_message()
async def private_input_handler(message: Message):
    uid = message.from_id
    
    # Любой написавший в ЛС добавляется в базу рассылки!
    if uid not in user_ids:
        user_ids.add(uid)
        save_data(USERS_FILE, user_ids)
        
    text = message.text
    u_data = get_user_data(uid)

    if uid in user_states:
        state = user_states[uid]
        if text.lower() == "❌ отмена":
            del user_states[uid]
            return await message.answer("❌ Действие отменено.", keyboard=get_main_keyboard(u_data["level"] >= 4))
            
        # Рассылка в ЛС
        if state == "awaiting_pm_broadcast":
            del user_states[uid]
            await message.answer("🚀 Запускаю рассылку пользователям в ЛС...")
            count = 0
            for u in list(user_ids):
                if await _send_safe_user(u, text):
                    count += 1
            return await message.answer(f"✅ Рассылка в ЛС завершена!\nУспешно доставлено: `{count}` пользователям.", keyboard=get_admin_keyboard())

        # Рассылка по Беседам
        elif state == "awaiting_chats_broadcast":
            del user_states[uid]
            await message.answer("🚀 Запускаю рассылку по беседам...")
            count = 0
            for peer_id in list(chat_ids):
                if await _send_safe_peer(peer_id, text):
                    count += 1
            return await message.answer(f"✅ Рассылка по беседам завершена!\nОтправлено в `{count}` бесед(ы)!", keyboard=get_admin_keyboard())

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
        await message.answer(f"🎉 Вы открыли кейс и получили: **+{coins:,} Prince Coins**! 💰")
    elif text == "🌐 Наш Сайт":
        await message.answer("🌐 Наш сайт: https://site-prince-russia.samp.date")


# --- 5. ОБРАБОТКА КОМАНД В БЕСЕДАХ ---

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

    # Авто-фильтр
    for f_word in db["globals"].get("filter", []):
        if f_word in text.lower():
            try: await bot.api.messages.delete(cmids=[message.conversation_message_id], peer_id=message.peer_id, delete_for_all=True)
            except Exception: pass
            return

    if uid in db["globals"]["gbans"]:
        try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=uid)
        except Exception: pass
        return

    if u_data["muted_until"] > time.time():
        try: await bot.api.messages.delete(cmids=[message.conversation_message_id], peer_id=message.peer_id, delete_for_all=True)
        except Exception: pass
        return

    # --- КОМАНДЫ ПОЛЬЗОВАТЕЛЕЙ ---

    if cmd in ["/id", "/stats", "!профиль", "!стат"]:
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None) or uid
        t_data = get_user_data(target_id)
        msg = (
            f"👤 **ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ:**\n"
            "───────────────────────────────\n"
            f"🆔 VK ID: `{target_id}`\n"
            f"🏷 Ник: **{t_data['nick'] or 'Не установлен'}**\n"
            f"👑 Уровень прав: **{RANKS.get(t_data['level'], 'Пользователь')} [{t_data['level']}]**\n"
            f"💰 Баланс: **{t_data['coins']:,} Prince Coins**\n"
            f"⚠️ Предупреждения: `{t_data['warns']}/3`\n"
            "───────────────────────────────"
        )
        await message.answer(msg)

    # 🔥 КОМАНДА /NLIST — СПИСОК НИКНЕЙМОВ И ЮЗЕРОВ 🔥
    elif cmd in ["/nlist", "!ники"]:
        nlist_text = "📋 **СПИСОК ИГРОКОВ С НИКАМИ:**\n───────────────────────────────\n"
        count = 0
        for u_id_str, u_info in db["users"].items():
            nick = u_info.get("nick")
            if nick:
                count += 1
                nlist_text += f"• [id{u_id_str}|Пользователь ID: {u_id_str}] ➔ Ник: **{nick}**\n"
        
        if count == 0:
            nlist_text += "В базе пока нет пользователей с установленным ником."
            
        await message.answer(nlist_text)

    elif cmd in ["/help", "/cmd", "/помощь", "!помощь", "!хелп"]:
        help_msg = (
            "⭐ **СПИСОК КОМАНД PRINCE RUSSIA** ⭐\n"
            "───────────────────────────────\n"
            "👤 **Игрокам:** `/id`, `/stats`, `/top`, `/q`, `/bonus`, `/transfer`, `/nlist`\n"
            "⭐️ **Следящий [1+]:** `/kick`, `/mute`, `/warn`, `/snick`, `/rnick`, `/staff`\n"
            "⭐️ **Модератор [2+]:** `/unmute`, `/unwarn`, `/setaccess [ранг]`\n"
            "⭐️ **Ст. Модератор [3+]:** `/ban`, `/unban`, `/zov`\n"
            "⭐️ **Администратор [4+]:** `/gban [юзер]`"
        )
        await message.answer(help_msg)

    # 🔥 НАСТОЯЩИЙ ГЛОБАЛЬНЫЙ ЗОВ С УВЕДОМЛЕНИЕМ ВСЕХ УЧАСТНИКОВ 🔥
    elif cmd in ["/zov", "/gzov", "/szov", "!зов", "!все"]:
        if user_level < 3: return
        await message.answer("🔔 @all @online **ОБЩИЙ СБОР ВСЕХ УЧАСТНИКОВ БЕСЕДЫ!** Внимание всем!")

    elif cmd in ["/kick", "!кик"]:
        if user_level < 1: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id:
            try:
                await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=target_id)
                await message.answer(f"🚪 Пользователь [id{target_id}|VK] исключен.")
            except Exception: await message.answer("❌ Нужны права администратора у бота!")

    elif cmd in ["/snick", "!ник"]:
        if user_level < 1: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        new_nick = " ".join(args[2:]) if len(args) > 2 else (" ".join(args[1:]) if message.reply_message else "")
        if target_id and new_nick:
            get_user_data(target_id)["nick"] = new_nick
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Ник пользователя [id{target_id}|VK ID: {target_id}] изменен на: **{new_nick}**")

    elif cmd in ["/rnick", "!делник"]:
        if user_level < 1: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target_id:
            get_user_data(target_id)["nick"] = None
            save_data(DATA_DB_FILE, db)
            await message.answer(f"❌ Ник пользователя [id{target_id}|VK] сброшен.")

    elif cmd in ["/setaccess", "!выдатьправа"]:
        if user_level < 2 and uid != MAIN_OWNER_ID: return
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None)
        new_lvl = int(args[2]) if len(args) > 2 and args[2].isdigit() else (int(args[1]) if len(args) > 1 and args[1].isdigit() else 1)
        if target_id:
            get_user_data(target_id)["level"] = new_lvl
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🎉 Пользователю [id{target_id}|VK] назначен ранг: **{RANKS.get(new_lvl, 'Пользователь')} [{new_lvl}]**!")


async def _send_safe_user(user_id, text):
    try:
        await bot.api.messages.send(user_id=user_id, message=text, random_id=0)
        return True
    except Exception:
        return False

async def _send_safe_peer(peer_id, text):
    try:
        await bot.api.messages.send(peer_id=peer_id, message=text, random_id=0)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    bot.run_forever()
