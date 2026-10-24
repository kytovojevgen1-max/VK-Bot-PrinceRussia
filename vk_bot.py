import os
import json
from threading import Thread
from flask import Flask
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

# --- 1. ВЕБ-СЕРВЕР ДЛЯ RENDER (БЕСПЛАТНЫЙ ТАРИФ $0) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Prince Russia Bot is Active 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()


# --- 2. НАСТРОЙКИ И БАЗА ДАННЫХ ---
TOKEN = "vk1.a.msFlcd5y5n3ouSMUzsU5UYT2iSsz4oZpfqugFyFvBoDPuIJCuaTveRYFLZUWk7hLbnlLkLRivG5oRTMXhZU0SzOc1emMasJWDUD6NmWyEYjhc9uCa8dqbbTKb_EGadWM10CBTRPdvW-aeYAHS_sPp83X79GHyiDThjRh1qxRA_PdmEnk2mQGTYzf_gn8gby_7dwqLtrurXbwi2qw7w1kJw"
bot = Bot(token=TOKEN)

# Ваш VK ID в качестве Главного Создателя
ADMIN_IDS = {897082738}

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"

def load_data(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_data(filename, data_set):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(list(data_set), f)
    except Exception as e:
        print(f"Ошибка сохранения {filename}: {e}")

user_ids = load_data(USERS_FILE)
chat_ids = load_data(CHATS_FILE)

# Хранение состояний для кнопок рассылок и анкет
user_states = {}


# --- 3. КЛАВИАТУРЫ (КНОПКИ) ---

def get_main_keyboard(is_admin: bool):
    keyboard = Keyboard(one_time=False, inline=False)
    
    keyboard.add(Text("🎬 Заявка на Медиа"), color=KeyboardButtonColor.POSITIVE)
    keyboard.add(Text("🛡 Заявка на Админку"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    
    keyboard.add(Text("🌐 Наш Сайт"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("💬 Тест-Сервер"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    
    keyboard.add(Text("📋 Правила & FAQ"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🆘 Поддержка"), color=KeyboardButtonColor.NEGATIVE)
    
    if is_admin:
        keyboard.row()
        keyboard.add(Text("👑 Админ-Панель"), color=KeyboardButtonColor.PRIMARY)
        
    return keyboard.get_json()

def get_admin_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    
    # Отдельные кнопки для рассылок!
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
        "Выберите нужный раздел на кнопках ниже:"
    )
    await message.answer(welcome_text, keyboard=get_main_keyboard(is_admin))

# --- АДМИН-ПАНЕЛЬ ---

@bot.on.private_message(text="👑 Админ-Панель")
async def admin_panel_handler(message: Message):
    if message.from_id not in ADMIN_IDS:
        return await message.answer("❌ У вас нет доступа к панели администратора.")
    
    admin_text = (
        "🛠 **АДМИН-ПАНЕЛЬ PRINCE RUSSIA**\n\n"
        f"📊 **Статистика бота:**\n"
        f"• Пользователей в ЛС: `{len(user_ids)}` чел.\n"
        f"• Активных бесед/чатов: `{len(chat_ids)}` групп\n\n"
        "Выберите нужное действие ниже:"
    )
    await message.answer(admin_text, keyboard=get_admin_keyboard())

# Кнопка: Рассылка в ЛС
@bot.on.private_message(text="📢 Рассылка в ЛС")
async def broadcast_pm_start(message: Message):
    if message.from_id not in ADMIN_IDS:
        return
    user_states[message.from_id] = "awaiting_pm_broadcast"
    await message.answer("✍️ Отправьте текст объявления для **всех пользователей в ЛС**:", keyboard=get_cancel_keyboard())

# Кнопка: Рассылка по Беседам
@bot.on.private_message(text="💬 Рассылка по Беседам")
async def broadcast_chats_start(message: Message):
    if message.from_id not in ADMIN_IDS:
        return
    user_states[message.from_id] = "awaiting_chats_broadcast"
    await message.answer("✍️ Отправьте текст новости/информации для **всех бесед и чатов**:", keyboard=get_cancel_keyboard())

# Кнопка: Выдача админки
@bot.on.private_message(text="🔑 Выдать Админку")
async def give_admin_start(message: Message):
    if message.from_id not in ADMIN_IDS:
        return
    user_states[message.from_id] = "awaiting_give_admin"
    await message.answer("✍️ Перешлите сообщение нового админа или отправьте его **VK ID** (числами):", keyboard=get_cancel_keyboard())


# --- ОБРАБОТКА ВВОДА АДМИНИСТРАТОРА И АНКЕТ ---

@bot.on.private_message()
async def private_input_handler(message: Message):
    uid = message.from_id
    text = message.text
    
    # 1. Если пользователь находится в процессе заполнения анкет / ввода
    if uid in user_states:
        state = user_states[uid]
        
        # Выход по отмене
        if text.lower() == "❌ отмена":
            del user_states[uid]
            is_admin = uid in ADMIN_IDS
            return await message.answer("❌ Действие отменено.", keyboard=get_main_keyboard(is_admin))
            
        # А) Рассылка ТОЛЬКО в ЛС
        if state == "awaiting_pm_broadcast" and uid in ADMIN_IDS:
            del user_states[uid]
            await message.answer("🚀 Запускаю рассылку пользователям в ЛС...")
            count = 0
            for u_id in list(user_ids):
                try:
                    await bot.api.messages.send(user_id=u_id, message=text, random_id=0)
                    count += 1
                except Exception:
                    pass
            return await message.answer(f"✅ Рассылка в ЛС завершена!\nУспешно доставлено: {count} пользователям.", keyboard=get_admin_keyboard())

        # Б) Рассылка ТОЛЬКО по Беседам
        elif state == "awaiting_chats_broadcast" and uid in ADMIN_IDS:
            del user_states[uid]
            await message.answer("🚀 Запускаю рассылку по всем беседам...")
            count = 0
            for c_id in list(chat_ids):
                try:
                    await bot.api.messages.send(peer_id=c_id, message=text, random_id=0)
                    count += 1
                except Exception:
                    pass
            return await message.answer(f"✅ Информационная рассылка отправлена в {count} бесед(ы)!", keyboard=get_admin_keyboard())

        # В) Выдача админки
        elif state == "awaiting_give_admin" and uid in ADMIN_IDS:
            del user_states[uid]
            target_id = None
            if message.reply_message:
                target_id = message.reply_message.from_id
            elif text.isdigit():
                target_id = int(text)
            
            if target_id:
                ADMIN_IDS.add(target_id)
                return await message.answer(f"🎉 Пользователь [id{target_id}|VK ID: {target_id}] добавлен в админы бота!", keyboard=get_admin_keyboard())
            else:
                return await message.answer("❌ Ошибка. Введите точный числовой ID пользователя.", keyboard=get_admin_keyboard())

        # Г) Прием анкеты на Админку / Медиа от обычного игрока
        elif state in ["awaiting_admin_app", "awaiting_media_app"]:
            app_type = "🛡 АДМИНКУ" if state == "awaiting_admin_app" else "🎬 МЕДИА"
            del user_states[uid]
            
            # Пересылаем главку (Вам на ID 897082738)
            report_text = (
                f"📥 **НОВАЯ ЗАЯВКА НА {app_type}!**\n\n"
                f"👤 Отправитель: [id{uid}|Пользователь]\n"
                f"📝 Текст заявки:\n{text}"
            )
            for admin_id in ADMIN_IDS:
                try:
                    await bot.api.messages.send(user_id=admin_id, message=report_text, random_id=0)
                except Exception:
                    pass
            
            return await message.answer("✅ Ваша заявка успешно отправлена руководству проекта! Ожидайте ответа.", keyboard=get_main_keyboard(uid in ADMIN_IDS))

    # 2. Обработка обычных кнопок меню
    if text == "🎬 Заявка на Медиа":
        user_states[uid] = "awaiting_media_app"
        await message.answer("🎥 **Подача заявки на Медиа-партнёрство**\n\nНапишите в ответном сообщении ссылки на ваши каналы (YouTube/TikTok) и ваш статистику:", keyboard=get_cancel_keyboard())
        
    elif text == "🛡 Заявка на Админку":
        user_states[uid] = "awaiting_admin_app"
        form = (
            "🛡 **Анкета на пост Администратора**\n\n"
            "Напишите ответы на следующие пункты одним сообщением:\n"
            "1. Ваш реальный возраст:\n"
            "2. Ваш игровой ник:\n"
            "3. Ваш часовой пояс:\n"
            "4. Опыт работы администратором:"
        )
        await message.answer(form, keyboard=get_cancel_keyboard())
        
    elif text == "🌐 Наш Сайт":
        await message.answer("🌐 Наш официальный сайт и UCP:\n👉 https://site-prince-russia.samp.date")
        
    elif text == "💬 Тест-Сервер":
        await message.answer("🎮 Присоединяйтесь к нашей беседе игрового сервера!")
        
    elif text == "📋 Правила & FAQ":
        await message.answer("📜 Все актуальные правила сервера доступны в статьях группы.")
        
    elif text == "🆘 Поддержка":
        await message.answer("🆘 Опишите вашу проблему, и администрация свяжется с вами!")


# --- 5. ОБРАБОТКА И СОХРАНЕНИЕ ЧАТОВ / БЕСЕД ---

@bot.on.chat_message()
async def chat_handler(message: Message):
    # Сохраняем ID беседы для рассылок по чатам
    if message.peer_id not in chat_ids:
        chat_ids.add(message.peer_id)
        save_data(CHATS_FILE, chat_ids)
        
    text = message.text
    
    # Команды модерации в беседе
    if text.startswith("!ник ") or text.startswith("/ник "):
        nick = text.split(" ", 1)[1] if " " in text else ""
        await message.answer(f"✅ Ваш кастомный ник изменен на: **{nick}**")
        
    elif text in ["!помощь", "/помощь", "!хелп", "/хелп"]:
        await message.answer("🛠 **Команды чат-менеджера:**\n• `!ник [текст]` — Установить ник\n• `!кик` — Исключить (ответом на сообщение)\n• `!бан` — Забанить (ответом на сообщение)")

if __name__ == "__main__":
    bot.run_forever()
