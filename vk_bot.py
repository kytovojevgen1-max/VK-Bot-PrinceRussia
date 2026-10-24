import os
import re
from vkbottle.bot import Bot, Message

# Токен встроен для проверки
TOKEN = "vk1.a.msFlcd5y5n3ouSMUzsU5UYT2iSsz4oZpfqugFyFvBoDPuIJCuaTveRYFLZUWk7hLbnlLkLRivG5oRTMXhZU0SzOc1emMasJWDUD6NmWyEYjhc9uCa8dqbbTKb_EGadWM10CBTRPdvW-aeYAHS_sPp83X79GHyiDThjRh1qxRA_PdmEnk2mQGTYzf_gn8gby_7dwqLtrurXbwi2qw7w1kJw"
bot = Bot(token=TOKEN)

# Хранилище ников пользователей: { (peer_id, user_id): "Ник" }
user_nicks = {}

# Хранилище забаненных пользователей для каждой беседы: { peer_id: set(user_ids) }
banned_users = {}


def get_user_mention(user_id: int) -> str:
    """Формирует упоминание пользователя"""
    return f"[id{user_id}|Пользователь]"


@bot.on.chat_message()
async def auto_check_ban(message: Message):
    """Авто-проверка: если вошел забаненный пользователь — сразу кикаем"""
    peer_id = message.peer_id
    from_id = message.from_id

    if peer_id in banned_users and from_id in banned_users[peer_id]:
        try:
            await bot.api.messages.remove_chat_user(
                chat_id=message.chat_id,
                member_id=from_id
            )
            await message.answer("🚫 Забаненный пользователь попытался написать и был исключен.")
            return
        except Exception:
            pass


# ==========================================
# КОМАНДЫ ДЛЯ РАБОТЫ С НИКАМИ
# ==========================================

@bot.on.chat_message(text=["!ник <nick>", "/ник <nick>"])
async def set_nick_handler(message: Message, nick: str):
    """Установка собственного ника"""
    if len(nick) > 30:
        return await message.answer("⚠️ Ник слишком длинный (максимум 30 символов).")

    key = (message.peer_id, message.from_id)
    user_nicks[key] = nick
    await message.answer(f"✅ Ваш ник в этой беседе изменен на: **{nick}**")


@bot.on.chat_message(text=["!делник", "/делник"])
async def del_nick_handler(message: Message):
    """Удаление своего ника"""
    key = (message.peer_id, message.from_id)
    if key in user_nicks:
        del user_nicks[key]
        await message.answer("❌ Ваш кастомный ник удален.")
    else:
        await message.answer("⚠️ У вас не был установлен кастомный ник.")


@bot.on.chat_message(text=["!мойник", "/мойник"])
async def my_nick_handler(message: Message):
    """Проверка текущего ника"""
    key = (message.peer_id, message.from_id)
    nick = user_nicks.get(key)
    if nick:
        await message.answer(f"👤 Ваш ник в беседе: **{nick}**")
    else:
        await message.answer("👤 У вас используется стандартное имя VK.")


# ==========================================
# КОМАНДЫ МОДЕРАЦИИ (КИК / БАН / РАЗБАН)
# ==========================================

@bot.on.chat_message(text=["!кик", "/кик"])
async def kick_handler(message: Message):
    """Кик пользователя из беседы (ответом на сообщение)"""
    if not message.reply_message:
        return await message.answer("⚠️ Ответьте на сообщение того, кого хотите кикнуть!")

    target_id = message.reply_message.from_id

    try:
        await bot.api.messages.remove_chat_user(
            chat_id=message.chat_id,
            member_id=target_id
        )
        await message.answer(f"🚪 {get_user_mention(target_id)} успешно исключен из беседы.")
    except Exception as e:
        await message.answer("❌ Не удалось кикнуть. Убедитесь, что бот является **администратором беседы** (выдана звездочка)!")


@bot.on.chat_message(text=["!бан", "/бан"])
async def ban_handler(message: Message):
    """Бан пользователя (кик + авто-кик при повторном входе)"""
    if not message.reply_message:
        return await message.answer("⚠️ Ответьте на сообщение того, кого хотите забанить!")

    target_id = message.reply_message.from_id
    peer_id = message.peer_id

    if peer_id not in banned_users:
        banned_users[peer_id] = set()

    banned_users[peer_id].add(target_id)

    try:
        await bot.api.messages.remove_chat_user(
            chat_id=message.chat_id,
            member_id=target_id
        )
        await message.answer(f"⛔ {get_user_mention(target_id)} забанен и исключен из беседы.")
    except Exception:
        await message.answer(f"⛔ {get_user_mention(target_id)} добавлен в черный список бота.")


@bot.on.chat_message(text=["!разбан", "/разбан"])
async def unban_handler(message: Message):
    """Разбан пользователя (ответом на сообщение)"""
    if not message.reply_message:
        return await message.answer("⚠️ Ответьте на сообщение того, кого хотите разбанить!")

    target_id = message.reply_message.from_id
    peer_id = message.peer_id

    if peer_id in banned_users and target_id in banned_users[peer_id]:
        banned_users[peer_id].remove(target_id)
        await message.answer(f"🟢 {get_user_mention(target_id)} разбанен и может снова зайти в беседу.")
    else:
        await message.answer("⚠️ Этот пользователь не был забанен.")


# ==========================================
# ПОМОЩЬ
# ==========================================

@bot.on.chat_message(text=["!помощь", "/помощь", "!хелп", "/хелп"])
async def help_handler(message: Message):
    help_text = (
        "🛠 **Список команд чат-менеджера:**\n\n"
        "📌 **Ники:**\n"
        "• `!ник [текст]` — Установить себе ник\n"
        "• `!делник` — Удалить свой ник\n"
        "• `!мойник` — Узнать свой ник\n\n"
        "🛡 **Модерация (работает ответом на сообщение):**\n"
        "• `!кик` — Исключить участника\n"
        "• `!бан` — Забанить участника (авто-кик)\n"
        "• `!разбан` — Снять бан с участника\n\n"
        "⚠️ *Не забудьте выдать боту права Администратора (звездочку) в беседе!*"
    )
    await message.answer(help_text)


if __name__ == "__main__":
    bot.run_forever()
