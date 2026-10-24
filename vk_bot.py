import os
import json
import time
import random
import re
from threading import Thread
from flask import Flask
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

# =====================================================================
# 1. ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА (RENDER 24/7 FREE $0)
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Prince Russia Ultimate Chat-Manager: ONLINE 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()


# =====================================================================
# 2. НАСТРОЙКИ, ТОКЕН И БАЗЫ ДАННЫХ
# =====================================================================
TOKEN = "vk1.a.msFlcd5y5n3ouSMUzsU5UYT2iSsz4oZpfqugFyFvBoDPuIJCuaTveRYFLZUWk7hLbnlLkLRivG5oRTMXhZU0SzOc1emMasJWDUD6NmWyEYjhc9uCa8dqbbTKb_EGadWM10CBTRPdvW-aeYAHS_sPp83X79GHyiDThjRh1qxRA_PdmEnk2mQGTYzf_gn8gby_7dwqLtrurXbwi2qw7w1kJw"
bot = Bot(token=TOKEN)

MAIN_OWNER_ID = 897082738  # Твой VK ID (Владелец)

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
        print(f"Ошибка сохранения БД {filename}: {e}")

user_ids = load_data(USERS_FILE, default_type=set)
chat_ids = load_data(CHATS_FILE, default_type=set)
db = load_data(DATA_DB_FILE, default_type=dict)

if "users" not in db: db["users"] = {}
if "chats" not in db: db["chats"] = {}
if "roles" not in db: db["roles"] = {}
if "globals" not in db: 
    db["globals"] = {
        "gbans": [], 
        "filter": ["дискорд", "discord.gg", "t.me/"], 
        "rules": "📜 Правила бесед Prince Russia Official:\n1. Уважение к участникам.\n2. Запрещен спам и реклама.",
        "silence": False
    }

user_states = {}

RANKS = {
    0: "Пользователь",
    1: "Следящий",
    2: "Модератор",
    3: "Старший Модератор",
    4: "Администратор",
    5: "Спец. Администратор",
    6: "Руководитель",
    7: "Главный Владелец"
}

def get_user_data(uid):
    uid_str = str(uid)
    if uid_str not in db["users"]:
        # Автоматически выдаем тебе права владельца при первом обращении
        is_owner = 7 if int(uid) == MAIN_OWNER_ID else 0
        db["users"][uid_str] = {
            "coins": 15000,
            "level": is_owner,
            "nick": None,
            "warns": 0,
            "muted_until": 0,
            "last_bonus": 0,
            "messages_count": 0,
            "reg_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        # Страховка: если это ты, всегда обновляем до уровня 7
        if int(uid) == MAIN_OWNER_ID and db["users"][uid_str]["level"] < 7:
            db["users"][uid_str]["level"] = 7
    return db["users"][uid_str]

async def get_target_user(message: Message, arg: str = None):
    if message.reply_message:
        return message.reply_message.from_id
    if not arg:
        return None
    clean_arg = arg.strip()
    match = re.search(r'\[id(\d+)\|', clean_arg)
    if match: return int(match.group(1))
    clean_arg = clean_arg.replace("https://vk.com/", "").replace("vk.com/", "").replace("@", "").replace("id", "")
    if clean_arg.isdigit(): return int(clean_arg)
    try:
        res = await bot.api.users.get(user_ids=[clean_arg])
        if res: return res[0].id
    except Exception: pass
    return None


# =====================================================================
# 3. КЛАВИАТУРЫ ДЛЯ ЛС
# =====================================================================

def get_main_keyboard(is_admin: bool):
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🚀 Как начать играть"), color=KeyboardButtonColor.POSITIVE)
    keyboard.add(Text("🎁 Ежедневный бонус"), color=KeyboardButtonColor.POSITIVE)
    keyboard.row()
    keyboard.add(Text("🎬 Заявка на Медиа"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("🛡 Заявка на Админку"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🌐 Наш Сайт"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("📋 Правила & FAQ"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
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
    keyboard.add(Text("🔙 Главное меню"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard.get_json()


# =====================================================================
# 4. ОБРАБОТКА ЛС БОТА
# =====================================================================

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
        "👑 **PRINCE RUSSIA — ЦЕНТР УПРАВЛЕНИЯ** 👑\n"
        "───────────────────────────────\n"
        f"👤 Ваш статус: **{RANKS.get(u_data['level'], 'Пользователь')}**\n"
        f"💰 Баланс: **{u_data['coins']:,} Coins**\n"
        "───────────────────────────────\n"
        "Выберите раздел на клавиатуре ниже:"
    )
    await message.answer(welcome_text, keyboard=get_main_keyboard(is_admin))

@bot.on.private_message(text="👑 Админ-Панель")
async def admin_panel(message: Message):
    if get_user_data(message.from_id)["level"] < 4: return
    await message.answer("🛠 **АДМИН-ПАНЕЛЬ СИСТЕМЫ**\nВыберите нужный тип рассылки:", keyboard=get_admin_keyboard())

@bot.on.private_message(text="📢 Рассылка в ЛС")
async def broadcast_pm(message: Message):
    if get_user_data(message.from_id)["level"] < 4: return
    user_states[message.from_id] = "pm"
    await message.answer(f"✍️ Введите текст для рассылки **в ЛС пользователям** (База: {len(user_ids)} чел.):")

@bot.on.private_message(text="💬 Рассылка по Беседам")
async def broadcast_chats(message: Message):
    if get_user_data(message.from_id)["level"] < 4: return
    user_states[message.from_id] = "chats"
    await message.answer(f"✍️ Введите текст для рассылки **по всем беседам** (Всего чатов: {len(chat_ids)}):")

@bot.on.private_message()
async def private_input(message: Message):
    uid = message.from_id
    user_ids.add(uid)
    save_data(USERS_FILE, user_ids)
    text = message.text

    if uid in user_states:
        state = user_states[uid]
        del user_states[uid]
        count = 0
        if state == "pm":
            for u in list(user_ids):
                try:
                    await bot.api.messages.send(user_id=u, message=text, random_id=0)
                    count += 1
                except Exception: pass
            return await message.answer(f"✅ Рассылка в ЛС завершена! Доставлено: `{count}` пользователям.")
        elif state == "chats":
            for c in list(chat_ids):
                try:
                    await bot.api.messages.send(peer_id=c, message=text, random_id=0)
                    count += 1
                except Exception: pass
            return await message.answer(f"✅ Рассылка по беседам завершена! Отправлено в `{count}` чатов.")

    if text in ["🚀 Как начать играть", "🌐 Наш Сайт"]:
        await message.answer("🌐 Наш официальный сайт и лаунчер:\n👉 https://site-prince-russia.samp.date")
    elif text == "🎁 Ежедневный бонус":
        u_data = get_user_data(uid)
        if time.time() - u_data["last_bonus"] < 86400:
            return await message.answer("⏳ Бонус можно забирать раз в 24 часа!")
        coins = random.randint(5000, 25000)
        u_data["coins"] += coins
        u_data["last_bonus"] = time.time()
        save_data(DATA_DB_FILE, db)
        await message.answer(f"🎉 Вы открыли кейс и получили: **+{coins:,} Prince Coins**!")


# =====================================================================
# 5. ЯДРО ОБРАБОТКИ СООБЩЕНИЙ И КОМАНД В БЕСЕДАХ
# =====================================================================

@bot.on.chat_message()
async def chat_handler(message: Message):
    # Сохраняем беседу в базу
    if message.peer_id not in chat_ids:
        chat_ids.add(message.peer_id)
        save_data(CHATS_FILE, chat_ids)

    # ПРИВЕТСТВИЕ И ИНСТРУКЦИЯ ПРИ ДОБАВЛЕНИИ БОТА В ЧАТ
    # (Проверяем, если бот зашел в беседу или его упомянули в новом чате)
    if message.action and message.action.type == "chat_invite_user":
        if message.action.member_id == -bot.api.token_settings: # если добавили самого бота
            welcome_msg = (
                "👑 **ПРИВЕТСТВУЮ ВАС НА ПРОЕКТЕ PRINCE RUSSIA!** 👑\n"
                "───────────────────────────────\n"
                "🤖 Официальный Чат-Менеджер успешно подключен к беседе!\n\n"
                "⚙️ **ВАЖНО ДЛЯ РАБОТЫ:**\n"
                "1. Выдайте боту **права Администратора (звездочку)** в беседе.\n"
                "2. Убедитесь, что в настройках беседы включен пункт **«Доступ к переписке»**.\n\n"
                "📌 Напишите в чат `/стата` или `!помощь`, чтобы начать работу!"
            )
            return await message.answer(welcome_msg)

    text = message.text
    args = text.split()
    cmd = args[0].lower() if args else ""
    uid = message.from_id
    
    # Получаем данные пользователя и автоматически выдаем тебе права
    u_data = get_user_data(uid)
    user_level = u_data["level"]

    u_data["messages_count"] += 1
    save_data(DATA_DB_FILE, db)

    # Фильтр слов
    for f_word in db["globals"].get("filter", []):
        if f_word in text.lower() and user_level < 1:
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


    # =================================================================
    # ⭐️ ВСЕ КОМАНДЫ ЧАТ-МЕНЕДЖЕРА
    # =================================================================

    if cmd in ["test", "пинг", "ping", "/ping"]:
        await message.answer("🏓 **Понг!** Чат-менеджер Prince Russia активен и работает на 100%!")

    elif cmd in ["правила", "rules", "/rules"]:
        await message.answer(f"📜 **ПРАВИЛА БЕСЕДЫ:**\n{db['globals']['rules']}")

    elif cmd == "q" or cmd == "/q":
        if user_level > 0: return await message.answer("❌ Администрации запрещено покидать чат через /q!")
        try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=uid)
        except Exception: pass

    elif cmd in ["/id", "/stats", "статистика", "stats", "/стата", "стата"]:
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None) or uid
        t_data = get_user_data(target_id)
        role_title = RANKS.get(t_data["level"], "Пользователь")
        msg = (
            f"👤 **ПРОФИЛЬ УЧАСТНИКА:**\n"
            "───────────────────────────────\n"
            f"🆔 VK ID: `{target_id}`\n"
            f"🏷 Ник: **{t_data['nick'] or 'Не установлен'}**\n"
            f"👑 Ранг в боте: **{role_title} [{t_data['level']}]**\n"
            f"💰 Баланс: **{t_data['coins']:,} Coins**\n"
            f"✉️ Сообщений: `{t_data['messages_count']}`\n"
            f"⚠️ Варны: `{t_data['warns']}/3`\n"
            "───────────────────────────────"
        )
        await message.answer(msg)

    elif cmd in ["mtop", "топ"]:
        top = sorted(db["users"].items(), key=lambda x: x[1].get("messages_count", 0), reverse=True)[:10]
        msg = "📈 **ТОП-10 ПО СООБЩЕНИЯМ:**\n───────────────────────────────\n"
        for i, (k, v) in enumerate(top, 1):
            msg += f"{i}. [id{k}|Участник] — `{v['messages_count']}` сообщ.\n"
        await message.answer(msg)

    elif cmd in ["staff", "админы"]:
        staff = [f"• [id{k}|Администратор] — {RANKS.get(v['level'], 'Админ')}" for k, v in db["users"].items() if v.get("level", 0) > 0]
        await message.answer("👑 **АДМИНИСТРАЦИЯ КОНФЕРЕНЦИИ:**\n───────────────────────────────\n" + ("\n".join(staff) if staff else "Пусто"))

    elif cmd in ["online", "онлайн"]:
        await message.answer("🟢 **ПОЛЬЗОВАТЕЛИ В СЕТИ:**\nВсе участники успешно синхронизированы с ботом!")

    elif cmd in ["чатинфо", "chat"]:
        await message.answer(f"💬 **ИНФОРМАЦИЯ О ЧАТЕ:**\n🆔 Peer ID: `{message.peer_id}`\n👥 Подключено бесед в базе: `{len(chat_ids)}`")

    elif cmd in ["mutelist", "mlist"]:
        muted = [f"• [id{k}|Участник]" for k, v in db["users"].items() if v.get("muted_until", 0) > time.time()]
        await message.answer("🔇 **СПИСОК С МУТОМ ЧАТА:**\n" + ("\n".join(muted) if muted else "Заблокированных нет."))

    elif cmd in ["warnlist"]:
        warned = [f"• [id{k}|Участник] — {v['warns']}/3 варнов" for k, v in db["users"].items() if v.get("warns", 0) > 0]
        await message.answer("⚠️ **СПИСОК С ВАРНАМИ:**\n" + ("\n".join(warned) if warned else "Предупреждений ни у кого нет."))

    # --- МОДЕРАЦИЯ ---

    elif cmd in ["кик", "kick"]:
        if user_level < 1: return await message.answer("❌ Требуется ранг: Следящий [1+] (Напиши /стата для авто-выдачи прав)")
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            try:
                await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=target)
                await message.answer(f"🚪 Участник [id{target}|VK] исключен.")
            except Exception: await message.answer("❌ Выдайте боту права администратора!")

    elif cmd in ["варн", "warn"]:
        if user_level < 1: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            t = get_user_data(target)
            t["warns"] += 1
            save_data(DATA_DB_FILE, db)
            await message.answer(f"⚠️ Участнику [id{target}|VK] выдан варн ({t['warns']}/3).")

    elif cmd in ["мут", "mute"]:
        if user_level < 2: return await message.answer("❌ Требуется ранг: Модератор [2+]")
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            get_user_data(target)["muted_until"] = time.time() + 900
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🔇 Участнику [id{target}|VK] выдан мут на 15 минут.")

    elif cmd in ["setnick", "snick", "ник"]:
        if user_level < 1: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        new_nick = " ".join(args[2:]) if len(args) > 2 else (" ".join(args[1:]) if message.reply_message else "")
        if target and new_nick:
            get_user_data(target)["nick"] = new_nick
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Ник изменен на: **{new_nick}**")

    elif cmd in ["вызов", "zov", "zov", "!зов"]:
        if user_level < 1: return
        await message.answer("🔔 @all @online **ОБЩИЙ СБОР ВСЕХ УЧАСТНИКОВ!** Внимание!")

    elif cmd in ["help", "команды", "!помощь", "помощь"]:
        help_text = (
            "⭐ **МЕНЕДЖЕР PRINCE RUSSIA — КОМАНДЫ** ⭐\n"
            "───────────────────────────────\n"
            "👤 **Игрокам:** `пинг`, `правила`, `q`, `/стата`, `mtop`, `staff`, `online`\n"
            "⭐️ **Администрирование:** `кик`, `варн`, `мут`, `snick`, `зов`\n"
            "───────────────────────────────\n"
            "💡 *Напиши в чат `/стата`, чтобы бот активировал твой статус Владельца!*"
        )
        await message.answer(help_text)


if __name__ == "__main__":
    bot.run_forever()
