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
    return "Prince Russia Ultimate Megabot Core: ACTIVE 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()


# =====================================================================
# 2. НАСТРОЙКИ, ТОКЕН И БАЗЫ ДАННЫХ
# =====================================================================
TOKEN = "vk1.a.msFlcd5y5n3ouSMUzsU5UYT2iSsz4oZpfqugFyFvBoDPuIJCuaTveRYFLZUWk7hLbnlLkLRivG5oRTMXhZU0SzOc1emMasJWDUD6NmWyEYjhc9uCa8dqbbTKb_EGadWM10CBTRPdvW-aeYAHS_sPp83X79GHyiDThjRh1qxRA_PdmEnk2mQGTYzf_gn8gby_7dwqLtrurXbwi2qw7w1kJw"
bot = Bot(token=TOKEN)

MAIN_OWNER_ID = 897082738  # Твой Главный VK ID (Владелец)

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
# Локальные данные по чатам: чат -> юзер -> {nick, role, warns, muted}
if "chat_members" not in db: db["chat_members"] = {}
# Локальные роли по чатам: чат -> {название_роли: приоритет}
if "chat_roles" not in db: db["chat_roles"] = {}

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

def get_user_global(uid):
    uid_str = str(uid)
    if uid_str not in db["users"]:
        is_owner = 7 if int(uid) == MAIN_OWNER_ID else 0
        db["users"][uid_str] = {
            "coins": 15000,
            "level": is_owner,
            "global_nick": None,
            "messages_count": 0,
            "reg_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        if int(uid) == MAIN_OWNER_ID and db["users"][uid_str]["level"] < 7:
            db["users"][uid_str]["level"] = 7
    return db["users"][uid_str]

def get_chat_member(peer_id, uid):
    peer_str = str(peer_id)
    uid_str = str(uid)
    if peer_str not in db["chat_members"]:
        db["chat_members"][peer_str] = {}
    if uid_str not in db["chat_members"][peer_str]:
        db["chat_members"][peer_str][uid_str] = {
            "nick": None,
            "role": None,
            "warns": 0,
            "muted_until": 0
        }
    return db["chat_members"][peer_str][uid_str]

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
    keyboard.add(Text("💬 Рассылка по Пулу Бесед"), color=KeyboardButtonColor.PRIMARY)
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
    g_data = get_user_global(uid)
    save_data(DATA_DB_FILE, db)
    
    if uid in user_states: del user_states[uid]
    is_admin = g_data["level"] >= 4 or uid == MAIN_OWNER_ID
    
    welcome_text = (
        "👑 **PRINCE RUSSIA — ЦЕНТР УПРАВЛЕНИЯ** 👑\n"
        "───────────────────────────────\n"
        f"👤 Ваш статус: **{RANKS.get(g_data['level'], 'Пользователь')}**\n"
        f"💰 Баланс: **{g_data['coins']:,} Coins**\n"
        "───────────────────────────────\n"
        "Выберите раздел на клавиатуре ниже:"
    )
    await message.answer(welcome_text, keyboard=get_main_keyboard(is_admin))

@bot.on.private_message(text="👑 Админ-Панель")
async def admin_panel(message: Message):
    if get_user_global(message.from_id)["level"] < 4: return
    await message.answer("🛠 **АДМИН-ПАНЕЛЬ СИСТЕМЫ**\nВыберите нужный тип рассылки:", keyboard=get_admin_keyboard())

@bot.on.private_message(text="📢 Рассылка в ЛС")
async def broadcast_pm(message: Message):
    if get_user_global(message.from_id)["level"] < 4: return
    user_states[message.from_id] = "pm"
    await message.answer(f"✍️ Введите текст для рассылки **в ЛС пользователям** (База: {len(user_ids)} чел.):")

@bot.on.private_message(text="💬 Рассылка по Пулу Бесед")
async def broadcast_chats(message: Message):
    if get_user_global(message.from_id)["level"] < 4: return
    user_states[message.from_id] = "chats"
    await message.answer(f"✍️ Введите текст для рассылки **по привязанным чатам пула** (Всего чатов в пуле: {len(chat_ids)}):")

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
            return await message.answer(f"✅ Рассылка по пулу завершена! Отправлено в `{count}` чатов.")

    if text in ["🚀 Как начать играть", "🌐 Наш Сайт"]:
        await message.answer("🌐 Наш официальный сайт и лаунчер:\n👉 https://site-prince-russia.samp.date")
    elif text == "🎁 Ежедневный бонус":
        g_data = get_user_global(uid)
        if time.time() - g_data["last_bonus"] < 86400:
            return await message.answer("⏳ Бонус можно забирать раз в 24 часа!")
        coins = random.randint(5000, 25000)
        g_data["coins"] += coins
        g_data["last_bonus"] = time.time()
        save_data(DATA_DB_FILE, db)
        await message.answer(f"🎉 Вы открыли кейс и получили: **+{coins:,} Prince Coins**!")


# =====================================================================
# 5. ЯДРО ОБРАБОТКИ СООБЩЕНИЙ И КОМАНД В БЕСЕДАХ
# =====================================================================

@bot.on.chat_message()
async def chat_handler(message: Message):
    peer = message.peer_id
    uid = message.from_id

    # Приветствие при добавлении бота в чат
    if message.action and message.action.type == "chat_invite_user":
        if message.action.member_id == -bot.api.token_settings:
            welcome_msg = (
                "👑 **ПРИВЕТСТВУЮ ВАС НА ПРОЕКТЕ PRINCE RUSSIA!** 👑\n"
                "───────────────────────────────\n"
                "🤖 Официальный Чат-Менеджер успешно подключен!\n\n"
                "⚙️ **ИНСТРУКЦИЯ:**\n"
                "1. Выдайте боту **права Администратора (звездочку)**.\n"
                "2. Если хотите добавить этот чат в глобальный пул, введите `/pull`.\n"
                "3. Напишите `/стата`, чтобы активировать права Владельца!"
            )
            return await message.answer(welcome_msg)

    text = message.text
    args = text.split()
    cmd = args[0].lower() if args else ""
    
    g_data = get_user_global(uid)
    m_data = get_chat_member(peer, uid)
    user_level = g_data["level"]

    g_data["messages_count"] += 1
    save_data(DATA_DB_FILE, db)

    # Фильтр слов
    for f_word in db["globals"].get("filter", []):
        if f_word in text.lower() and user_level < 1:
            try: await bot.api.messages.delete(cmids=[message.conversation_message_id], peer_id=peer, delete_for_all=True)
            except Exception: pass
            return

    if uid in db["globals"]["gbans"]:
        try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=uid)
        except Exception: pass
        return

    if m_data["muted_until"] > time.time():
        try: await bot.api.messages.delete(cmids=[message.conversation_message_id], peer_id=peer, delete_for_all=True)
        except Exception: pass
        return


    # =================================================================
    # ⭐️ ЛОКАЛЬНЫЕ КОМАНДЫ ЧАТА (РАБОТАЮТ ТОЛЬКО ЗДЕСЬ)
    # =================================================================

    if cmd in ["test", "пинг", "ping", "/ping"]:
        is_pulled = "Да (В пуле)" if peer in chat_ids else "Нет (Обычный чат)"
        await message.answer(f"🏓 **Понг!** Чат-менеджер активен.\n📌 Статус чата: **{is_pulled}**")

    elif cmd in ["правила", "rules", "/rules"]:
        await message.answer(f"📜 **ПРАВИЛА БЕСЕДЫ:**\n{db['globals']['rules']}")

    elif cmd == "q" or cmd == "/q":
        if user_level > 0: return await message.answer("❌ Администрации запрещено покидать чат через /q!")
        try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=uid)
        except Exception: pass

    elif cmd in ["/id", "/stats", "статистика", "stats", "/стата", "стата"]:
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None) or uid
        t_mdata = get_chat_member(peer, target_id)
        t_gdata = get_user_global(target_id)
        role_title = t_mdata["role"] or RANKS.get(t_gdata["level"], "Пользователь")
        msg = (
            f"👤 **ПРОФИЛЬ УЧАСТНИКА (В ЭТОМ ЧАТЕ):**\n"
            "───────────────────────────────\n"
            f"🆔 VK ID: `{target_id}`\n"
            f"🏷 Ник в этом чате: **{t_mdata['nick'] or 'Не установлен'}**\n"
            f"👑 Роль в этом чате: **{role_title}**\n"
            f"💰 Баланс: **{t_gdata['coins']:,} Coins**\n"
            f"⚠️ Варны в этом чате: `{t_mdata['warns']}/3`\n"
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
        await message.answer("👑 **АДМИНИСТРАЦИЯ:**\n───────────────────────────────\n" + ("\n".join(staff) if staff else "Пусто"))

    elif cmd in ["online", "онлайн"]:
        await message.answer("🟢 **ПОЛЬЗОВАТЕЛИ В СЕТИ:**\nВсе участники на связи!")

    elif cmd in ["чатинфо", "chat"]:
        is_p = "Да" if peer in chat_ids else "Нет"
        await message.answer(f"💬 **ИНФОРМАЦИЯ О ЧАТЕ:**\n🆔 Peer ID: `{peer}`\n🌐 Подключен к пулу: **{is_p}**")

    # --- ЛОКАЛЬНАЯ МОДЕРАЦИЯ И НИКИ (ТОЛЬКО ДЛЯ ЭТОГО ЧАТА) ---

    elif cmd in ["кик", "kick", "/kick"]:
        if user_level < 1: return await message.answer("❌ Требуется ранг: Следящий [1+] (Напиши /стата)")
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            try:
                await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=target)
                await message.answer(f"🚪 Участник [id{target}|VK] исключен из этого чата.")
            except Exception: await message.answer("❌ Выдайте боту права администратора!")

    elif cmd in ["варн", "warn", "/warn"]:
        if user_level < 1: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            t = get_chat_member(peer, target)
            t["warns"] += 1
            save_data(DATA_DB_FILE, db)
            await message.answer(f"⚠️ Участнику [id{target}|VK] выдан варн в этом чате ({t['warns']}/3).")

    elif cmd in ["мут", "mute", "/mute"]:
        if user_level < 2: return await message.answer("❌ Требуется ранг: Модератор [2+]")
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            get_chat_member(peer, target)["muted_until"] = time.time() + 900
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🔇 Участнику [id{target}|VK] выдан мут в этом чате на 15 минут.")

    elif cmd in ["setnick", "snick", "/snick", "ник", "!ник"]:
        if user_level < 1: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        new_nick = " ".join(args[2:]) if len(args) > 2 else (" ".join(args[1:]) if message.reply_message else "")
        if target and new_nick:
            get_chat_member(peer, target)["nick"] = new_nick
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Установлен ник **{new_nick}** для [id{target}|участника] (строго в этом чате).")

    elif cmd in ["removenick", "rnick", "/rnick", "рник"]:
        if user_level < 1: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            get_chat_member(peer, target)["nick"] = None
            save_data(DATA_DB_FILE, db)
            await message.answer("❌ Никнейм сброшен в этом чате.")

    elif cmd in ["nicklist", "nlist", "/nlist"]:
        peer_str = str(peer)
        nlist = []
        if peer_str in db["chat_members"]:
            for u_id_str, u_info in db["chat_members"][peer_str].items():
                if u_info.get("nick"):
                    nlist.append(f"• [id{u_id_str}|ID {u_id_str}] ➔ **{u_info['nick']}**")
        await message.answer("📋 **СПИСОК НИКОВ В ЭТОМ ЧАТЕ:**\n───────────────────────────────\n" + ("\n".join(nlist) if nlist else "Пусто"))

    # --- СОЗДАНИЕ И ВЫДАЧА РОЛЕЙ В ЭТОМ ЧАТЕ ---

    elif cmd in ["новаяроль"]:
        if user_level < 2: return await message.answer("❌ Нужен ранг Модератор [2+]")
        if len(args) >= 3 and args[1].isdigit():
            prio = int(args[1])
            r_name = " ".join(args[2:])
            peer_str = str(peer)
            if peer_str not in db["chat_roles"]: db["chat_roles"][peer_str] = {}
            db["chat_roles"][peer_str][r_name] = prio
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🎉 В этом чате создана роль **{r_name}** с приоритетом `{prio}`!")

    elif cmd in ["удалитьроль"]:
        if user_level < 2: return
        r_name = " ".join(args[1:])
        peer_str = str(peer)
        if peer_str in db["chat_roles"] and r_name in db["chat_roles"][peer_str]:
            del db["chat_roles"][peer_str][r_name]
            save_data(DATA_DB_FILE, db)
            await message.answer(f"❌ Роль **{r_name}** удалена в этом чате.")

    elif cmd in ["роли"]:
        peer_str = str(peer)
        r_list = "🎭 **РОЛИ ЭТОГО ЧАТА:**\n───────────────────────────────\n"
        if peer_str in db["chat_roles"]:
            for r_n, r_p in db["chat_roles"][peer_str].items():
                r_list += f"• Приоритет `{r_p}` ➔ **{r_n}**\n"
        await message.answer(r_list if peer_str in db["chat_roles"] and db["chat_roles"][peer_str] else "В этом чате нет кастомных ролей.")

    elif cmd in ["role", "роль", "/role"] and len(args) >= 3:
        if user_level < 2: return
        target = await get_target_user(message, args[1])
        r_name = " ".join(args[2:])
        if target:
            get_chat_member(peer, target)["role"] = r_name
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ В этом чате участнику [id{target}|VK] назначена роль: **{r_name}**!")

    elif cmd in ["вызов", "zov", "zov", "/zov", "!зов"]:
        if user_level < 1: return
        await message.answer("🔔 @all @online **ОБЩИЙ СБОР В ЭТОМ ЧАТЕ!** Внимание!")


    # =================================================================
    # ⭐️ УПРАВЛЕНИЕ ПУЛОМ БЕСЕД (/pull, /rpull)
    # =================================================================

    elif cmd in ["pull", "/pull"]:
        if peer not in chat_ids:
            chat_ids.add(peer)
            save_data(CHATS_FILE, chat_ids)
        await message.answer(f"🌐 **Чат успешно подключен к глобальному пулу!**\nВсего бесед в пуле: `{len(chat_ids)}`")

    elif cmd in ["rpull", "/rpull"]:
        if peer in chat_ids:
            chat_ids.remove(peer)
            save_data(CHATS_FILE, chat_ids)
        await message.answer("❌ Чат отключен от глобального пула.")


    # =================================================================
    # ⭐️ ГЛОБАЛЬНЫЕ КОМАНДЫ ПУЛА (ТОЛЬКО ТАМ, ГДЕ ЕСТЬ /pull)
    # =================================================================

    elif cmd in ["gsnick", "/gsnick"]:
        if peer not in chat_ids:
            return await message.answer("❌ Этот чат **не подключен к пулу**! Сначала введите `/pull` для привязки.")
        if user_level < 4: return await message.answer("❌ Требуется ранг Администратор [4+]!")
        
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        new_nick = " ".join(args[2:]) if len(args) > 2 else (" ".join(args[1:]) if message.reply_message else "")
        if target and new_nick:
            # Меняем ник во всех чатах пула для этого пользователя!
            for p_id in chat_ids:
                get_chat_member(p_id, target)["nick"] = new_nick
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🌐 **ПУЛ:** Ник пользователя [id{target}|VK] изменен на **{new_nick}** во всех чатах пула!")

    elif cmd in ["gkick", "/gkick"]:
        if peer not in chat_ids: return await message.answer("❌ Чат не в пуле! Используйте `/pull`.")
        if user_level < 4: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            count = 0
            for p in list(chat_ids):
                try:
                    await bot.api.messages.remove_chat_user(chat_id=p - 2000000000, member_id=target)
                    count += 1
                except Exception: pass
            await message.answer(f"⛔ **ПУЛ КИК:** Участник удален из `{count}` бесед пула.")

    elif cmd in ["gban", "/gban"]:
        if peer not in chat_ids: return await message.answer("❌ Чат не в пуле! Используйте `/pull`.")
        if user_level < 4: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            if target not in db["globals"]["gbans"]: db["globals"]["gbans"].append(target)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"⛔ **ПУЛ БАН:** Пользователь [id{target}|VK] занесен в черный список всего пула!")

    elif cmd in ["gmute", "/gmute"]:
        if peer not in chat_ids: return await message.answer("❌ Чат не в пуле! Используйте `/pull`.")
        if user_level < 4: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            for p in chat_ids:
                get_chat_member(p, target)["muted_until"] = time.time() + 3600
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🔇 **ПУЛ МУТ:** Пользователю [id{target}|VK] ограничен чат на 1 час во всех чатах пула.")

    elif cmd in ["gzov", "/gzov"]:
        if peer not in chat_ids: return await message.answer("❌ Чат не в пуле! Используйте `/pull`.")
        if user_level < 4: return
        txt = " ".join(args[1:]) if len(args) > 1 else "Глобальный сбор пула"
        count = 0
        for p in list(chat_ids):
            try:
                await bot.api.messages.send(peer_id=p, message=f"🔔 @all @online **ГЛОБАЛЬНЫЙ СБОР ПУЛА:** {txt}", random_id=0)
                count += 1
            except Exception: pass
        await message.answer(f"📢 Глобальный вызов отправлен в `{count}` привязанных бесед пула!")

    elif cmd in ["help", "команды", "!помощь", "/help", "помощь"]:
        help_text = (
            "⭐ **ПРОЕКТ PRINCE RUSSIA — ЧАТ-МЕНЕДЖЕР** ⭐\n"
            "───────────────────────────────\n"
            "👤 **Игрокам:** `пинг`, `правила`, `q`, `/стата`, `mtop`, `staff`, `online`\n"
            "⭐️ **Локально:** `кик`, `варн`, `мут`, `snick`, `rnick`, `nlist`, `новаяроль`, `роль`\n"
            "🌐 **Только через Пул (`/pull`):** `gsnick`, `gkick`, `gban`, `gmute`, `gzov`\n"
            "───────────────────────────────\n"
            "💡 *Напиши `/стата`, чтобы активировать права Владельца!*"
        )
        await message.answer(help_text)


if __name__ == "__main__":
    bot.run_forever()
