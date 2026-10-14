import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import random
import json
import os
import time
from flask import Flask
from threading import Thread
from datetime import datetime

TOKEN = "vk1.a.DBef1krkkTAEv6ephod0b8DA0z4zAUsisx0zPSph5i_gBWdt4B4OQnaBh1nuodWgxqfi5o3wLkkmVdvdqnsL-FIf4logWXo5fyeSjrmnAK5eMJNewdSuCBvFhMsP-TR5fdgozZmi1uNIT3lwRCAPJA5UJ_S1brxlxxSqUliNaj5g12aqE-CtFuH8oOaxAa6dSA3SflDe2nBXB9pksBUnig"
DEV_ID = 897082738  # Твой цифровой VK ID (Владелец)

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

DB_FILE = "vk_database.json"

# --- МИНИ-СЕРВЕР ДЛЯ RENDER (24/7) ---
app = Flask('')

@app.route('/')
def home():
    return "Prince Russia VK God Mode Engine is Online & Running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
# -------------------------------------

CAN_MANAGE_PREFIXES = ["💻 Разработчик", "👑 Владелец Проекта", "🔱 Зам. Владельца"]

# --- БАЗА ДАННЫХ ---
def load_data():
    default_data = {
        "admins": {DEV_ID},
        "admin_prefixes": {str(DEV_ID): "💻 Разработчик"},
        "all_users": {DEV_ID},
        "banned_users": set(),
        "user_scores": {},
        "daily_bonus": {},
        "promo_codes": {},
        "used_promos": {},
        "silent_mode": False,
        "test_server_open": False
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                admins = set(data.get("admins", [DEV_ID]))
                admins.add(DEV_ID)
                all_users = set(data.get("all_users", [DEV_ID]))
                all_users.add(DEV_ID)
                banned_users = set(data.get("banned_users", []))
                admin_prefixes = data.get("admin_prefixes", {})
                admin_prefixes[str(DEV_ID)] = "💻 Разработчик"

                return {
                    "admins": admins,
                    "admin_prefixes": admin_prefixes,
                    "all_users": all_users,
                    "banned_users": banned_users,
                    "user_scores": data.get("user_scores", {}),
                    "daily_bonus": data.get("daily_bonus", {}),
                    "promo_codes": data.get("promo_codes", {}),
                    "used_promos": data.get("used_promos", {}),
                    "silent_mode": data.get("silent_mode", False),
                    "test_server_open": data.get("test_server_open", False)
                }
        except Exception:
            return default_data
    return default_data

def save_data():
    data_to_save = {
        "admins": list(db["admins"]),
        "admin_prefixes": db["admin_prefixes"],
        "all_users": list(db["all_users"]),
        "banned_users": list(db["banned_users"]),
        "user_scores": db["user_scores"],
        "daily_bonus": db["daily_bonus"],
        "promo_codes": db["promo_codes"],
        "used_promos": db["used_promos"],
        "silent_mode": db["silent_mode"],
        "test_server_open": db["test_server_open"]
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

db = load_data()
user_states = {}
test_applications = {}
pending_test_actions = {}

def get_user_name(user_id):
    try:
        user_info = vk.users.get(user_id=user_id)[0]
        return f"{user_info['first_name']} {user_info['last_name']}"
    except Exception:
        return f"ID{user_id}"

def register_user(user_id):
    is_new = user_id not in db["all_users"]
    db["all_users"].add(user_id)
    if str(user_id) not in db["user_scores"]:
        db["user_scores"][str(user_id)] = 500
    save_data()

    if is_new and user_id not in db["admins"] and not db["silent_mode"]:
        name = get_user_name(user_id)
        notify_text = f"🚀 [VK GOD MODE: НОВЫЙ ИГРОК]\n👤 Имя: {name}\n🆔 ID: {user_id}\n📊 Всего игроков: {len(db['all_users'])}"
        for admin_id in db["admins"]:
            try:
                vk.messages.send(user_id=admin_id, message=notify_text, random_id=get_random_id())
            except Exception: pass

# --- КЛАВИАТУРЫ VK ---
def get_main_keyboard(user_id):
    keyboard = {
        "inline": True,
        "buttons": [
            [
                {"action": {"type": "text", "payload": "{\"cmd\": \"profile\"}", "label": "👤 Профиль"}, "color": "primary"},
                {"action": {"type": "text", "payload": "{\"cmd\": \"daily\"}", "label": "🎁 Бонус"}, "color": "positive"}
            ],
            [
                {"action": {"type": "text", "payload": "{\"cmd\": \"case\"}", "label": "📦 Кейс 🎁"}, "color": "secondary"},
                {"action": {"type": "text", "payload": "{\"cmd\": \"top\"}", "label": "🏆 ТОП Богачей"}, "color": "secondary"}
            ],
            [
                {"action": {"type": "text", "payload": "{\"cmd\": \"promo\"}", "label": "🎟 Промокод"}, "color": "secondary"},
                {"action": {"type": "text", "payload": "{\"cmd\": \"casino\"}", "label": "🎰 Казино 👑"}, "color": "negative"}
            ],
            [
                {"action": {"type": "text", "payload": "{\"cmd\": \"test_server\"}", "label": "🧪 Тест-Сервер"}, "color": "secondary"},
                {"action": {"type": "text", "payload": "{\"cmd\": \"rules\"}", "label": "📜 Правила"}, "color": "secondary"}
            ]
        ]
    }
    if user_id in db["admins"]:
        keyboard["buttons"].append([
            {"action": {"type": "text", "payload": "{\"cmd\": \"admin_panel\"}", "label": "⚡️ ПАНЕЛЬ ОЛИГАРХА"}, "color": "negative"}
        ])
    return json.dumps(keyboard, ensure_ascii=False)

def get_admin_keyboard():
    keyboard = {
        "inline": True,
        "buttons": [
            [
                {"action": {"type": "text", "payload": "{\"cmd\": \"adm_stats\"}", "label": "📊 Статистика"}, "color": "primary"},
                {"action": {"type": "text", "payload": "{\"cmd\": \"adm_list\"}", "label": "📋 Список админов"}, "color": "primary"}
            ],
            [
                {"action": {"type": "text", "payload": "{\"cmd\": \"adm_toggle_test\"}", "label": "🔓/🔒 Статус теста"}, "color": "secondary"},
                {"action": {"type": "text", "payload": "{\"cmd\": \"adm_toggle_silent\"}", "label": "🔕 Тихий режим"}, "color": "secondary"}
            ],
            [
                {"action": {"type": "text", "payload": "{\"cmd\": \"menu\"}", "label": "🔙 Главное меню"}, "color": "negative"}
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def send_msg(user_id, message, keyboard=None):
    try:
        post_data = {
            "user_id": user_id,
            "message": message,
            "random_id": get_random_id()
        }
        if keyboard:
            post_data["keyboard"] = keyboard
        vk.messages.send(**post_data)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

# --- ОСНОВНОЙ ЦИКЛ ОБРАБОТКИ СООБЩЕНИЙ VK ---
def start_bot():
    print("✅ VK Бот успешно запущен и ожидает сообщения!")
    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    user_id = event.user_id
                    text = event.text.strip()
                    register_user(user_id)

                    if user_id in db["banned_users"]:
                        send_msg(user_id, "⛔️ Доступ к боту заблокирован!")
                        continue

                    state = user_states.get(user_id)
                    user_bal = db["user_scores"].get(str(user_id), 0)

                    # Обработка кнопок и текстовых команд
                    if text.lower() in ["/start", "начать", "меню", "🔙 главное меню", '{"cmd": "menu"}']:
                        user_states[user_id] = None
                        name = get_user_name(user_id)
                        welcome_text = (
                            f"👑 PRINCE RUSSIA — VK GOD MODE ENGINE 🔥\n"
                            f"───────────────────────────────\n"
                            f"Привет, {name}!\n"
                            f"💰 Твой баланс: {user_bal} Prince Coins\n\n"
                            f"Выбирай нужную кнопку ниже:"
                        )
                        send_msg(user_id, welcome_text, get_main_keyboard(user_id))
                        continue

                    # Профиль
                    elif text == "👤 Профиль" or text == '{"cmd": "profile"}':
                        role = db["admin_prefixes"].get(str(user_id), "👑 Элитный Игрок")
                        msg = (
                            f"👤 КАРТОЧКА ИГРОКА — PRINCE RUSSIA\n"
                            f"───────────────────────────────\n"
                            f"🆔 VK ID: {user_id}\n"
                            f"📛 Статус: {role}\n"
                            f"💰 Баланс: {user_bal} Prince Coins\n"
                            f"🛡 Репутация: 100% GOD MODE"
                        )
                        send_msg(user_id, msg, get_main_keyboard(user_id))

                    # Ежедневный бонус
                    elif text == "🎁 Бонус" or text == '{"cmd": "daily"}':
                        today = datetime.now().strftime("%Y-%m-%d")
                        last_claim = db["daily_bonus"].get(str(user_id))
                        if last_claim == today:
                            send_msg(user_id, "⏳ Бонус уже получен сегодня! Заглядывай завтра.", get_main_keyboard(user_id))
                            continue
                        db["daily_bonus"][str(user_id)] = today
                        bonus = random.randint(200, 500)
                        db["user_scores"][str(user_id)] = user_bal + bonus
                        save_data()
                        send_msg(user_id, f"🎁 Бонус забран! Получено: +{bonus} Prince Coins 🔥", get_main_keyboard(user_id))

                    # Кейс
                    elif text == "📦 Кейс 🎁" or text == '{"cmd": "case"}':
                        if user_bal < 250:
                            send_msg(user_id, "❌ Недостаточно коинов! Нужно минимум 250 Coins.", get_main_keyboard(user_id))
                            continue
                        db["user_scores"][str(user_id)] -= 250
                        win = random.randint(100, 1500)
                        db["user_scores"][str(user_id)] += win
                        save_data()
                        send_msg(user_id, f"📦 Кейс открыт! Твой выигрыш: +{win} Prince Coins! 🚀", get_main_keyboard(user_id))

                    # ТОП
                    elif text == "🏆 ТОП Богачей" or text == '{"cmd": "top"}':
                        sorted_users = sorted(db["user_scores"].items(), key=lambda x: x[1], reverse=True)[:10]
                        top_text = "🏆 ТОП-10 ОЛИГАРХОВ ПРОЕКТА\n───────────────────────────────\n"
                        for idx, (uid, score) in enumerate(sorted_users, 1):
                            name = get_user_name(int(uid))
                            top_text += f"{idx}. {name} — {score} Coins\n"
                        send_msg(user_id, top_text, get_main_keyboard(user_id))

                    # Промокод (Шаг 1)
                    elif text == "🎟 Промокод" or text == '{"cmd": "promo"}':
                        user_states[user_id] = 'enter_promo'
                        send_msg(user_id, "🎟 Введи секретный промокод в чат:")

                    elif state == 'enter_promo':
                        user_states[user_id] = None
                        code = text.upper()
                        if code in db["promo_codes"]:
                            used = db["used_promos"].get(str(user_id), [])
                            if code in used:
                                send_msg(user_id, "❌ Ты уже активировал этот промокод!", get_main_keyboard(user_id))
                                continue
                            reward = db["promo_codes"][code]
                            db["user_scores"][str(user_id)] = user_bal + reward
                            used.append(code)
                            db["used_promos"][str(user_id)] = used
                            save_data()
                            send_msg(user_id, f"🎉 Промокод {code} активирован! Получено: +{reward} Coins!", get_main_keyboard(user_id))
                        else:
                            send_msg(user_id, "❌ Неверный промокод.", get_main_keyboard(user_id))

                    # Казино кости
                    elif text == "🎰 Казино 👑" or text == '{"cmd": "casino"}':
                        send_msg(user_id, "🎰 Введи ставку в Coins для игры в кости:")
                        user_states[user_id] = 'casino_bet'

                    elif state == 'casino_bet':
                        user_states[user_id] = None
                        if text.isdigit():
                            bet = int(text)
                            if bet <= 0 or bet > user_bal:
                                send_msg(user_id, "❌ Неверная ставка!", get_main_keyboard(user_id))
                                continue
                            db["user_scores"][str(user_id)] -= bet
                            dice_user = random.randint(1, 6)
                            dice_bot = random.randint(1, 6)
                            if dice_user >= dice_bot:
                                win = bet * 2
                                db["user_scores"][str(user_id)] += win
                                save_data()
                                send_msg(user_id, f"🎲 Твои очки: {dice_user} | Бот: {dice_bot}\n🎉 Ты выиграл {win} Coins!", get_main_keyboard(user_id))
                            else:
                                save_data()
                                send_msg(user_id, f"🎲 Твои очки: {dice_user} | Бот: {dice_bot}\n😢 Ты проиграл {bet} Coins.", get_main_keyboard(user_id))

                    # Админ-панель
                    elif text == "⚡️ ПАНЕЛЬ ОЛИГАРХА" or text == '{"cmd": "admin_panel"}':
                        if user_id in db["admins"]:
                            send_msg(user_id, "⚡️ Панель Высшего Руководства:", get_admin_keyboard())
                        else:
                            send_msg(user_id, "❌ Нет доступа.")

                    elif text == '{"cmd": "adm_stats"}' and user_id in db["admins"]:
                        t_status = "ОТКРЫТ 🔓" if db["test_server_open"] else "ЗАКРЫТ 🔒"
                        stat_msg = f"📊 Статистика:\nИгроков: {len(db['all_users'])}\nАдминов: {len(db['admins'])}\nТест: {t_status}"
                        send_msg(user_id, stat_msg, get_admin_keyboard())

                    elif text == '{"cmd": "adm_list"}' and user_id in db["admins"]:
                        list_msg = "📋 Список администраторов:\n"
                        for adm in db["admins"]:
                            pref = db["admin_prefixes"].get(str(adm), "Админ")
                            list_msg += f"• ID{adm} — {pref}\n"
                        send_msg(user_id, list_msg, get_admin_keyboard())

                    elif text == '{"cmd": "adm_toggle_test"}' and user_id in db["admins"]:
                        db["test_server_open"] = not db["test_server_open"]
                        save_data()
                        st = "ОТКРЫТ 🔓" if db["test_server_open"] else "ЗАКРЫТ 🔒"
                        send_msg(user_id, f"✅ Набор теперь {st}", get_admin_keyboard())

                    else:
                        send_msg(user_id, "ℹ️ Воспользуйся кнопками меню:", get_main_keyboard(user_id))

        except Exception as e:
            print(f"⚠️ Ошибка LongPoll: {e}")
            time.sleep(3)

if __name__ == '__main__':
    print("🚀 Запуск фонового потока VK-бота...")
    bot_thread = Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    print("🚀 Запуск веб-сервера Flask для Render...")
    keep_alive()
    app.run(host='0.0.0.0', port=8080)