import os
from threading import Thread
from flask import Flask
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

# --- ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА (чтобы сервис был FREE $0) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Prince Russia Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()


# --- НАСТРОЙКА БОТА ---
TOKEN = "vk1.a.msFlcd5y5n3ouSMUzsU5UYT2iSsz4oZpfqugFyFvBoDPuIJCuaTveRYFLZUWk7hLbnlLkLRivG5oRTMXhZU0SzOc1emMasJWDUD6NmWyEYjhc9uCa8dqbbTKb_EGadWM10CBTRPdvW-aeYAHS_sPp83X79GHyiDThjRh1qxRA_PdmEnk2mQGTYzf_gn8gby_7dwqLtrurXbwi2qw7w1kJw"
bot = Bot(token=TOKEN)

user_nicks = {}
banned_users = {}


# --- СОЗДАНИЕ КНОПОК ДЛЯ ЛС (КЛАВИАТУРА) ---
def get_main_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    
    # Ряд 1
    keyboard.add(Text("🎬 Заявка на Медиа"), color=KeyboardButtonColor.POSITIVE)
    keyboard.add(Text("🛡 Заявка на Админку"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    
    # Ряд 2
    keyboard.add(Text("🌐 Наш Сайт"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("💬 Тест-Сервер"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    
    # Ряд 3
    keyboard.add(Text("📋 Правила & FAQ"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🆘 Поддержка"), color=KeyboardButtonColor.NEGATIVE)
    
    return keyboard.get_json()


# --- ОБРАБОТКА КОМАНД В ЛС (КНОПКИ) ---

@bot.on.private_message(text=["/start", "Начать", "начать", "Меню", "меню", "Старт"])
async def start_handler(message: Message):
    welcome_text = (
        "👑 **ДОБРО ПОЖАЛОВАТЬ В PRINCE RUSSIA OFFICIAL!** 👑\n\n"
        "Привет! Я официальный бот проекта Prince Russia.\n"
        "Используй меню с кнопками ниже, чтобы быстро подать заявку или получить информацию!"
    )
    await message.answer(welcome_text, keyboard=get_main_keyboard())

@bot.on.private_message(text="🎬 Заявка на Медиа")
async def media_handler(message: Message):
    text = (
        "🎥 **Подача заявки на Медиа-партнёрство**\n\n"
        "Требования:\n"
        "• YouTube / TikTok / VK Клипы\n"
        "• Регулярные видео по нашему проекту\n\n"
        "Для подачи заявки отпишите Главному Администратору или зашлите анкету на сайт:\n"
        "👉 https://site-prince-russia.samp.date"
    )
    await message.answer(text)

@bot.on.private_message(text="🛡 Заявка на Админку")
async def admin_handler(message: Message):
    text = (
        "🛡 **Подача заявки на пост Администратора**\n\n"
        "Анкета:\n"
        "1. Ваш реальный возраст (14+):\n"
        "2. Ваш игровой ник:\n"
        "3. Ваш часовой пояс:\n"
        "4. Опыт работы админом (да/нет):\n\n"
        "Отправьте ответы следующим сообщением!"
    )
    await message.answer(text)

@bot.on.private_message(text="🌐 Наш Сайт")
async def site_handler(message: Message):
    await message.answer("🌐 Наш официальный сайт и UCP: https://site-prince-russia.samp.date")

@bot.on.private_message(text="💬 Тест-Сервер")
async def test_server_handler(message: Message):
    await message.answer("🎮 Присоединяйся к нашему тест-серверу и беседe проекта!")

@bot.on.private_message(text="📋 Правила & FAQ")
async def rules_handler(message: Message):
    await message.answer("📜 Правила сервера и ответы на частые вопросы доступны во вкладке «Статьи» нашей группы.")

@bot.on.private_message(text="🆘 Поддержка")
async def support_handler(message: Message):
    await message.answer("🆘 Опишите вашу проблему, и наша администрация ответит вам в ближайшее время!")


# --- ОБРАБОТКА КОМАНД В БЕСЕДАХ (МОДЕРАЦИЯ) ---

def get_user_mention(user_id: int) -> str:
    return f"[id{user_id}|Пользователь]"

@bot.on.chat_message(text=["!ник <nick>", "/ник <nick>"])
async def set_nick_handler(message: Message, nick: str):
    if len(nick) > 30:
        return await message.answer("⚠️ Ник слишком длинный (макс 30 символов).")
    key = (message.peer_id, message.from_id)
    user_nicks[key] = nick
    await message.answer(f"✅ Ваш ник в беседе изменен на: **{nick}**")

@bot.on.chat_message(text=["!кик", "/кик"])
async def kick_handler(message: Message):
    if not message.reply_message:
        return await message.answer("⚠️ Ответьте на сообщение того, кого хотите кикнуть!")
    target_id = message.reply_message.from_id
    try:
        await bot.api.messages.remove_chat_user(chat_id=message.chat_id, member_id=target_id)
        await message.answer(f"🚪 {get_user_mention(target_id)} успешно исключен.")
    except Exception:
        await message.answer("❌ Не удалось кикнуть. Убедитесь, что у бота есть звездочка (админка)!")

@bot.on.chat_message(text=["!помощь", "/помощь", "!хелп", "/хелп"])
async def help_handler(message: Message):
    help_text = (
        "🛠 **Команды в беседе:**\n"
        "• `!ник [текст]` — Сменить ник в чате\n"
        "• `!кик` — Исключить участника (ответом)\n"
        "• `!бан` — Забанить участника (ответом)"
    )
    await message.answer(help_text)

if __name__ == "__main__":
    bot.run_forever()
