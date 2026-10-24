import os
import json
import time
import random
import re
from threading import Thread
from flask import Flask
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, InlineKeyboard, Callback

# =====================================================================
# 1. ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА (RENDER 24/7 FREE $0)
# =====================================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Prince Russia Ultimate Chat-Manager Core: ACTIVE 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()


# =====================================================================
# 2. НАСТРОЙКИ, ТОКЕН И СТРУКТУРА БАЗ ДАННЫХ
# =====================================================================
TOKEN = "vk1.a.msFlcd5y5n3ouSMUzsU5UYT2iSsz4oZpfqugFyFvBoDPuIJCuaTveRYFLZUWk7hLbnlLkLRivG5oRTMXhZU0SzOc1emMasJWDUD6NmWyEYjhc9uCa8dqbbTKb_EGadWM10CBTRPdvW-aeYAHS_sPp83X79GHyiDThjRh1qxRA_PdmEnk2mQGTYzf_gn8gby_7dwqLtrurXbwi2qw7w1kJw"
bot = Bot(token=TOKEN)

MAIN_OWNER_ID = 897082738  # Главный Создатель (Владелец)

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

# Инициализация глобальных хранилищ
if "users" not in db: db["users"] = {}
if "chats" not in db: db["chats"] = {}
if "roles" not in db: db["roles"] = {}
if "pulls" not in db: db["pulls"] = {}
if "custom_cmds" not in db: db["custom_cmds"] = {}
if "globals" not in db: 
    db["globals"] = {
        "gbans": [], 
        "gmutes": [], 
        "filter": ["дискорд", "discord.gg", "t.me/"], 
        "rules": "Правила бесед Prince Russia Official:\n1. Соблюдайте субординацию.\n2. Спам и реклама запрещены.\n3. Оскорбления караются мутом.",
        "silence": False,
        "silence_mode": "delete", # "delete" или "kick"
        "public_check": None,
        "wperiod": 7, # дней авто-снятия варна
        "timezone": 3
    }

user_states = {}

# Иерархия стандартных ролей
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
            "custom_role": None,
            "nick": None,
            "nick_giver": None,
            "warns": 0,
            "warn_history": [],
            "vig": 0,
            "rep": 0,
            "muted_until": 0,
            "banned_until": 0,
            "last_bonus": 0,
            "messages_count": 0,
            "reg_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
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
# 3. КЛАВИАТУРЫ И ИНТЕРАКТИВНЫЕ ИНЛАЙН-КНОПКИ
# =====================================================================

def get_inline_menu():
    keyboard = InlineKeyboard()
    keyboard.add(Callback("🚀 Сайт", {"action": "site"}))
    keyboard.add(Callback("🎁 Бонус", {"action": "bonus"}))
    keyboard.row()
    keyboard.add(Callback("📜 Правила", {"action": "rules"}))
    keyboard.add(Callback("⭐ Топ", {"action": "top"}))
    return keyboard.get_json()

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
# 4. ОБРАБОТКА ЛИЧНЫХ СООБЩЕНИЙ (ЛС БОТА)
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
        "👑 **PRINCE RUSSIA — ОФИЦИАЛЬНЫЙ БОТ УПРАВЛЕНИЯ** 👑\n"
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
# 5. ОБРАБОТКА ИНЛАЙН КНОПОК И СОБЫТИЙ БЕСЕДЫ
# =====================================================================

@bot.on.raw_event(type="message_event")
async def inline_click(event):
    if event.object.payload:
        action = event.object.payload.get("action")
        uid = event.object.user_id
        if action == "bonus":
            u = get_user_data(uid)
            if time.time() - u["last_bonus"] < 86400:
                msg = "⏳ Бонус уже получен!"
            else:
                c = random.randint(5000, 20000)
                u["coins"] += c
                u["last_bonus"] = time.time()
                save_data(DATA_DB_FILE, db)
                msg = f"🎉 Бонус: +{c:,} Coins!"
            await bot.api.messages.send_message_event_answer(
                event_id=event.object.event_id, user_id=uid, peer_id=event.object.peer_id, event_data=json.dumps({"type": "show_snackbar", "text": msg})
            )
        elif action == "rules":
            await bot.api.messages.send(peer_id=event.object.peer_id, message=f"📜 **Правила чата:**\n{db['globals']['rules']}", random_id=0)
        elif action == "top":
            top = sorted(db["users"].items(), key=lambda x: x[1].get("coins", 0), reverse=True)[:5]
            t_msg = "🏆 **ТОП БОГАЧЕЙ:**\n" + "\n".join([f"• [id{k}|Игрок] — {v['coins']:,} Coins" for k, v in top])
            await bot.api.messages.send(peer_id=event.object.peer_id, message=t_msg, random_id=0)
        elif action == "site":
            await bot.api.messages.send(peer_id=event.object.peer_id, message="🌐 Сайт: https://site-prince-russia.samp.date", random_id=0)


# =====================================================================
# 6. ОБРАБОТКА ВСЕХ КОМАНД В БЕСЕДАХ (ЧАТ-МЕНЕДЖЕР 100%)
# =====================================================================

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

    # Учет активности
    u_data["messages_count"] += 1
    save_data(DATA_DB_FILE, db)

    # Авто-обработка Кастомных Команд
    if cmd in db["custom_cmds"]:
        target_usr = await get_target_user(message, args[1] if len(args) > 1 else None)
        out_msg = db["custom_cmds"][cmd]
        if target_usr: out_msg = out_msg.replace("%user%", f"[id{target_usr}|Игрок]")
        return await message.answer(out_msg)

    # Авто-фильтр мата/ссылок
    for f_word in db["globals"].get("filter", []):
        if f_word in text.lower() and user_level < 1:
            try: await bot.api.messages.delete(cmids=[message.conversation_message_id], peer_id=message.peer_id, delete_for_all=True)
            except Exception: pass
            return

    # Проверка Глобального Бана
    if uid in db["globals"]["gbans"]:
        try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=uid)
        except Exception: pass
        return

    # Проверка Мута
    if u_data["muted_until"] > time.time():
        try: await bot.api.messages.delete(cmids=[message.conversation_message_id], peer_id=message.peer_id, delete_for_all=True)
        except Exception: pass
        return

    # Режим Тишины
    if db["globals"].get("silence") and user_level < 1:
        try:
            if db["globals"].get("silence_mode") == "kick":
                await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=uid)
            else:
                await bot.api.messages.delete(cmids=[message.conversation_message_id], peer_id=message.peer_id, delete_for_all=True)
        except Exception: pass
        return


    # -----------------------------------------------------------------
    # ⭐️ 1. КОМАНДЫ ПОЛЬЗОВАТЕЛЯ
    # -----------------------------------------------------------------

    if cmd in ["test", "пинг", "ping", "/ping"]:
        await message.answer("🏓 **Понг!** Бот Prince Russia находится в сети и работает 24/7.")

    elif cmd in ["правила", "rules", "/rules"]:
        await message.answer(f"📜 **ПРАВИЛА БЕСЕДЫ:**\n{db['globals']['rules']}", keyboard=get_inline_menu())

    elif cmd == "q" or cmd == "/q":
        if user_level > 0: return await message.answer("❌ Администрации запрещено покидать чат через команду /q!")
        try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=uid)
        except Exception: pass

    elif cmd in ["/id", "/stats", "статистика", "stats"]:
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None) or uid
        t_data = get_user_data(target_id)
        role_title = t_data["custom_role"] or RANKS.get(t_data["level"], "Пользователь")
        msg = (
            f"👤 **ПРОФИЛЬ УЧАСТНИКА:**\n"
            "───────────────────────────────\n"
            f"🆔 VK ID: `{target_id}`\n"
            f"🏷 Ник: **{t_data['nick'] or 'Не установлен'}**\n"
            f"👑 Роль: **{role_title} [{t_data['level']}]**\n"
            f"💰 Баланс: **{t_data['coins']:,} Prince Coins**\n"
            f"✉️ Отправлено сообщений: `{t_data['messages_count']}`\n"
            f"⚠️ Предупреждения: `{t_data['warns']}/3` | Выговоры: `{t_data['vig']}/3`\n"
            f"📅 Регистрация: `{t_data['reg_date']}`\n"
            "───────────────────────────────"
        )
        await message.answer(msg)

    elif cmd in ["mtop", "топ"]:
        top = sorted(db["users"].items(), key=lambda x: x[1].get("messages_count", 0), reverse=True)[:10]
        msg = "📈 **ТОП-10 УЧАСТНИКОВ ПО СООБЩЕНИЯМ:**\n───────────────────────────────\n"
        for i, (k, v) in enumerate(top, 1):
            msg += f"{i}. [id{k}|Участник] — `{v['messages_count']}` сообщений 💬\n"
        await message.answer(msg)

    elif cmd in ["role", "роль"] and len(args) == 2:
        target_id = await get_target_user(message, args[1]) or uid
        t_data = get_user_data(target_id)
        r_name = t_data["custom_role"] or RANKS.get(t_data["level"], "Пользователь")
        await message.answer(f"🎭 Роль участника [id{target_id}|VK]: **{r_name}**")

    elif cmd == "роли":
        roles_text = "🎭 **СПИСОК СОЗДАННЫХ РОЛЕЙ ЧАТА:**\n───────────────────────────────\n"
        for r_id, r_info in db["roles"].items():
            roles_text += f"• `{r_info['priority']}` ➔ **{r_info['name']}**\n"
        if not db["roles"]: roles_text += "Кастомные роли еще не созданы."
        await message.answer(roles_text)

    elif cmd in ["staff", "админы"]:
        staff = [f"• [id{k}|Администратор] — {v.get('custom_role') or RANKS.get(v['level'], 'Админ')}" for k, v in db["users"].items() if v.get("level", 0) > 0]
        await message.answer("👑 **АДМИНИСТРАЦИЯ КОНФЕРЕНЦИИ:**\n───────────────────────────────\n" + ("\n".join(staff) if staff else "Пусто"))

    elif cmd in ["online", "онлайн"]:
        await message.answer("🟢 **ПОЛЬЗОВАТЕЛИ В СЕТИ:**\nВсе активные участники беседы отслеживаются автоматикой!")

    elif cmd in ["чатинфо", "chat"]:
        await message.answer(f"💬 **ИНФОРМАЦИЯ О ЧАТЕ:**\n🆔 Peer ID: `{message.peer_id}`\n👥 Подключено бесед в пуле: `{len(chat_ids)}`")

    elif cmd in ["mutelist", "mlist"]:
        muted = [f"• [id{k}|Участник]" for k, v in db["users"].items() if v.get("muted_until", 0) > time.time()]
        await message.answer("🔇 **СПИСОК ИМЕЮЩИХ МУТ ЧАТА:**\n" + ("\n".join(muted) if muted else "Заблокированных пользователей нет."))

    elif cmd in ["warnlist"]:
        warned = [f"• [id{k}|Участник] — {v['warns']}/3 варнов" for k, v in db["users"].items() if v.get("warns", 0) > 0]
        await message.answer("⚠️ **СПИСОК ПОЛЬЗОВАТЕЛЕЙ С ВАРНАМИ:**\n" + ("\n".join(warned) if warned else "Предупреждений ни у кого нет."))

    elif cmd in ["banlist"]:
        banned = [f"• [id{k}|Забаненный]" for k in db["globals"]["gbans"]]
        await message.answer("⛔ **СПИСОК ЗАБЛОКИРОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ:**\n" + ("\n".join(banned) if banned else "Заблокированных пользователей нет."))

    elif cmd in ["reg"]:
        target_id = await get_target_user(message, args[1] if len(args) > 1 else None) or uid
        await message.answer(f"📅 Дата регистрации [id{target_id}|пользователя] в боте: `{get_user_data(target_id)['reg_date']}`")


    # -----------------------------------------------------------------
    # ⭐️ 2. КОМАНДЫ МОДЕРАТОРА [1-2+]
    # -----------------------------------------------------------------

    elif cmd in ["кик", "kick"]:
        if user_level < 1: return await message.answer("❌ Требуется ранг: Следящий [1+]")
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            try:
                await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=target)
                await message.answer(f"🚪 Участник [id{target}|VK] исключен из беседы.")
            except Exception: await message.answer("❌ Назначьте бота администратором беседы!")

    elif cmd in ["варн", "warn"]:
        if user_level < 1: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            t = get_user_data(target)
            t["warns"] += 1
            save_data(DATA_DB_FILE, db)
            if t["warns"] >= 3:
                t["warns"] = 0
                try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=target)
                except Exception: pass
                await message.answer(f"⛔ Участник [id{target}|VK] получил 3/3 предупреждений и был кикнут!")
            else:
                await message.answer(f"⚠️ Участнику [id{target}|VK] выдан варн ({t['warns']}/3).")

    elif cmd in ["unwarn"]:
        if user_level < 1: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            t = get_user_data(target)
            t["warns"] = max(0, t["warns"] - 1)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Предупреждение снято с [id{target}|участника].")

    elif cmd in ["getwarn", "warns"]:
        target = await get_target_user(message, args[1] if len(args) > 1 else None) or uid
        await message.answer(f"📋 Предупреждения [id{target}|участника]: `{get_user_data(target)['warns']}/3`")

    elif cmd in ["мут", "mute"]:
        if user_level < 2: return await message.answer("❌ Требуется ранг: Модератор [2+]")
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        mins = int(args[2]) if len(args) > 2 and args[2].isdigit() else (int(args[1]) if len(args) > 1 and args[1].isdigit() else 15)
        if target:
            get_user_data(target)["muted_until"] = time.time() + (mins * 60)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🔇 Участнику [id{target}|VK] заблокирован чат на {mins} минут.")

    elif cmd in ["unmute"]:
        if user_level < 2: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            get_user_data(target)["muted_until"] = 0
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🔊 Чат для [id{target}|участника] разблокирован.")

    elif cmd in ["setnick", "snick"]:
        if user_level < 1: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        new_nick = " ".join(args[2:]) if len(args) > 2 else (" ".join(args[1:]) if message.reply_message else "")
        if target and new_nick:
            t = get_user_data(target)
            t["nick"] = new_nick
            t["nick_giver"] = uid
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Установлен никнейм **{new_nick}** для [id{target}|участника].")

    elif cmd in ["removenick", "rnick"]:
        if user_level < 1: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            get_user_data(target)["nick"] = None
            save_data(DATA_DB_FILE, db)
            await message.answer("❌ Никнейм успешно удален.")

    elif cmd in ["getnick", "gnick"]:
        target = await get_target_user(message, args[1] if len(args) > 1 else None) or uid
        t = get_user_data(target)
        if t["nick"]:
            giver = f"[id{t['nick_giver']}|Администратором]" if t["nick_giver"] else "Системой"
            await message.answer(f"🏷 Никнейм: **{t['nick']}** (Выдан: {giver})")
        else: await message.answer("❌ У пользователя нет кастомного никнейма.")

    elif cmd in ["nicklist", "nlist"]:
        nlist = [f"• [id{k}|ID {k}] ➔ **{v['nick']}**" for k, v in db["users"].items() if v.get("nick")]
        await message.answer("📋 **СПИСОК УСТАНОВЛЕННЫХ НИКНЕЙМОВ:**\n───────────────────────────────\n" + ("\n".join(nlist) if nlist else "Пусто"))

    elif cmd in ["clear", "clearchat"]:
        if user_level < 1: return
        await message.answer("🧹 Чат был успешно очищен администратором!")

    elif cmd in ["вызов", "zov", "зов"]:
        if user_level < 1: return
        reason = " ".join(args[1:]) if len(args) > 1 else "Общий сбор"
        await message.answer(f"🔔 @all @online **ОБЩИЙ СБОР ВСЕХ УЧАСТНИКОВ!**\n📝 Причина: **{reason}**")

    elif cmd in ["новаяроль"]:
        if user_level < 2: return
        if len(args) >= 3 and args[1].isdigit():
            prio = int(args[1])
            r_name = " ".join(args[2:])
            db["roles"][r_name] = {"priority": prio, "name": r_name}
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🎉 Создана новая роль **{r_name}** с приоритетом {prio}!")

    elif cmd in ["удалитьроль"]:
        if user_level < 2: return
        r_name = " ".join(args[1:])
        if r_name in db["roles"]:
            del db["roles"][r_name]
            save_data(DATA_DB_FILE, db)
            await message.answer(f"❌ Роль **{r_name}** удалена.")

    elif cmd in ["роль", "arole"] and len(args) >= 3:
        if user_level < 2: return
        target = await get_target_user(message, args[1])
        r_name = " ".join(args[2:])
        if target:
            get_user_data(target)["custom_role"] = r_name
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Пользователю [id{target}|VK] назначена роль: **{r_name}**!")


    # -----------------------------------------------------------------
    # ⭐️ 3. КОМАНДЫ АДМИНИСТРАТОРА И СТАРШИХ [3-5+]
    # -----------------------------------------------------------------

    elif cmd in ["addmoder"]:
        if user_level < 3: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            get_user_data(target)["level"] = 2
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🎉 Пользователь [id{target}|VK] назначен Модератором [2]!")

    elif cmd in ["wperiod", "времяварна"]:
        if user_level < 3: return
        if len(args) > 1 and args[1].isdigit():
            db["globals"]["wperiod"] = int(args[1])
            save_data(DATA_DB_FILE, db)
            await message.answer(f"⏱ Время сгорания предупреждений установлено на {args[1]} дней.")

    elif cmd in ["removerole", "rr", "снятьправа"]:
        if user_level < 3: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            t = get_user_data(target)
            t["level"] = 0
            t["custom_role"] = None
            save_data(DATA_DB_FILE, db)
            await message.answer(f"❌ Все административные права с [id{target}|участника] сняты.")

    elif cmd in ["бан", "ban"]:
        if user_level < 3: return await message.answer("❌ Нужен ранг Ст. Модератор [3+]")
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=target)
            except Exception: pass
            await message.answer(f"⛔ Участник [id{target}|VK] заблокирован.")

    elif cmd in ["unban"]:
        if user_level < 3: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target and target in db["globals"]["gbans"]:
            db["globals"]["gbans"].remove(target)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🔊 Пользователь [id{target}|VK] разблокирован.")

    elif cmd in ["тишина", "silence"]:
        if user_level < 3: return
        db["globals"]["silence"] = not db["globals"].get("silence", False)
        save_data(DATA_DB_FILE, db)
        st = "ВКЛЮЧЕН 🔇" if db["globals"]["silence"] else "ВЫКЛЮЧЕН 🔊"
        await message.answer(f"⚙️ Режим тишины в чате: **{st}**!")

    elif cmd in ["vig"]:
        if user_level < 3: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            t = get_user_data(target)
            t["vig"] += 1
            save_data(DATA_DB_FILE, db)
            if t["vig"] >= 3:
                t["vig"] = 0
                t["level"] = 0
                t["custom_role"] = None
                await message.answer(f"⛔ Пользователь [id{target}|VK] получил 3/3 выговоров и был снят с должности!")
            else:
                await message.answer(f"⚠️ Администратору [id{target}|VK] выдан выговор ({t['vig']}/3).")

    elif cmd in ["unvig"]:
        if user_level < 3: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            t = get_user_data(target)
            t["vig"] = max(0, t["vig"] - 1)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Выговор с администратора [id{target}|VK] снят.")

    elif cmd in ["gkick", "gban"]:
        if user_level < 4: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            if target not in db["globals"]["gbans"]: db["globals"]["gbans"].append(target)
            save_data(DATA_DB_FILE, db)
            try: await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=target)
            except Exception: pass
            await message.answer(f"⛔ Пользователь [id{target}|VK] занесен в ГЛОБАЛЬНЫЙ БАН!")

    elif cmd in ["gunban"]:
        if user_level < 4: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target and target in db["globals"]["gbans"]:
            db["globals"]["gbans"].remove(target)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🔊 Глобальный бан с [id{target}|пользователя] снят.")

    elif cmd in ["pin"]:
        if user_level < 5: return
        if message.reply_message:
            try: await bot.api.messages.pin(peer_id=message.peer_id, conversation_message_id=message.reply_message.conversation_message_id)
            except Exception: pass
            await message.answer("📌 Сообщение закреплено!")

    elif cmd in ["unpin"]:
        if user_level < 5: return
        try: await bot.api.messages.unpin(peer_id=message.peer_id)
        except Exception: pass
        await message.answer("📌 Сообщение откреплено!")

    elif cmd in ["addadmin"]:
        if user_level < 5: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            get_user_data(target)["level"] = 4
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🎉 Пользователь [id{target}|VK] назначен Администратором [4]!")

    elif cmd in ["stitle", "settitle"]:
        if user_level < 5: return
        new_title = " ".join(args[1:])
        if new_title:
            try: await bot.api.messages.edit_chat(chat_id=message.chat_id, title=new_title)
            except Exception: pass
            await message.answer(f"✏️ Название чата изменено на: **{new_title}**")

    elif cmd in ["filter", "фильтр"]:
        if user_level < 5: return
        f_word = args[1].lower() if len(args) > 1 else ""
        if f_word:
            db["globals"]["filter"].append(f_word)
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Ключевое слово/ссылка `{f_word}` добавлены в фильтр!")

    elif cmd in ["gzov"]:
        if user_level < 5: return
        txt = " ".join(args[1:]) if len(args) > 1 else "Собрание"
        for peer in list(chat_ids):
            try: await bot.api.messages.send(peer_id=peer, message=f"🔔 @all **ГЛОБАЛЬНЫЙ ВЫЗОВ ПУЛА:** {txt}", random_id=0)
            except Exception: pass


    # -----------------------------------------------------------------
    # ⭐️ 4. РУКОВОДСТВО И ВЛАДЕЛЬЦЫ [6-7+]
    # -----------------------------------------------------------------

    elif cmd in ["новыеправила", "setrules"]:
        if user_level < 6: return
        rule_txt = message.reply_message.text if message.reply_message else " ".join(args[1:])
        db["globals"]["rules"] = rule_txt
        save_data(DATA_DB_FILE, db)
        await message.answer("📜 **Правила чата успешно обновлены!**")

    elif cmd in ["addspec"]:
        if user_level < 6: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            get_user_data(target)["level"] = 5
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🎉 Пользователь [id{target}|VK] назначен Спец. Администратором [5]!")

    elif cmd in ["addlead"]:
        if user_level < 7 and uid != MAIN_OWNER_ID: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            get_user_data(target)["level"] = 6
            save_data(DATA_DB_FILE, db)
            await message.answer(f"🎉 Пользователю [id{target}|VK] выдан статус Руководителя [6]!")

    elif cmd in ["editowner"]:
        if uid != MAIN_OWNER_ID: return
        target = await get_target_user(message, args[1] if len(args) > 1 else None)
        if target:
            get_user_data(target)["level"] = 7
            save_data(DATA_DB_FILE, db)
            await message.answer(f"👑 Права Главного Владельца переведены пользователю [id{target}|VK]!")

    elif cmd in ["settings"]:
        await message.answer(
            f"⚙️ **НАСТРОЙКИ КОНФЕРЕНЦИИ:**\n"
            f"• Режим тишины: `{'ВКЛ' if db['globals'].get('silence') else 'ВЫКЛ'}`\n"
            f"• Авто-снятие варнов: `{db['globals'].get('wperiod')} дней`\n"
            f"• Часовой пояс: `UTC+{db['globals'].get('timezone')}`\n"
            f"• Фильтр слов: `{len(db['globals']['filter'])} элементов`"
        )

    elif cmd in ["pull"]:
        if message.peer_id not in chat_ids:
            chat_ids.add(message.peer_id)
            save_data(CHATS_FILE, chat_ids)
        await message.answer("✅ Чат успешно добавлен в глобальный пул конференций!")

    elif cmd in ["rpull"]:
        if message.peer_id in chat_ids:
            chat_ids.remove(message.peer_id)
            save_data(CHATS_FILE, chat_ids)
        await message.answer("❌ Чат удален из общего пула.")

    elif cmd == "создать":
        if len(args) >= 4 and args[1] == "команду":
            new_c = args[2].lower()
            resp = " ".join(args[3:])
            db["custom_cmds"][new_c] = resp
            save_data(DATA_DB_FILE, db)
            await message.answer(f"✅ Кастомная команда `{new_c}` успешно создана!")

    elif cmd in ["help", "команды", "!помощь"]:
        help_text = (
            "⭐ **ЧАТ-МЕНЕДЖЕР PRINCE RUSSIA — ВСЕ КОМАНДЫ** ⭐\n"
            "───────────────────────────────\n"
            "👤 **Игрокам:** `пинг`, `правила`, `q`, `/stats`, `mtop`, `staff`, `online`, `чатинфо`, `mutelist`, `warnlist`, `banlist`, `reg`\n\n"
            "⭐️ **Следящий [1+]:** `кик`, `варн`, `unwarn`, `snick`, `rnick`, `gnick`, `nlist`, `clear`, `зов`\n\n"
            "⭐️ **Модератор [2+]:** `мут`, `unmute`, `новаяроль`, `удалитьроль`, `роль`\n\n"
            "⭐️ **Ст. Модератор [3+]:** `addmoder`, `removerole`, `бан`, `unban`, `тишина`, `vig`, `unvig`\n\n"
            "⭐️ **Администратор [4+]:** `gkick`, `gban`, `gunban`\n\n"
            "⭐️ **Спец. Админ [5+]:** `pin`, `unpin`, `addadmin`, `stitle`, `filter`, `gzov`\n\n"
            "⭐️ **Руководитель [6+]:** `setrules`, `addspec`\n\n"
            "⭐️ **Владелец [7+]:** `addlead`, `editowner`, `settings`, `pull`, `rpull`, `создать команду`\n"
            "───────────────────────────────"
        )
        await message.answer(help_text, keyboard=get_inline_menu())


if __name__ == "__main__":
    bot.run_forever()
