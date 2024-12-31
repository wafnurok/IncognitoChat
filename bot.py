from aiogram.types import Message
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command, CommandStart
from database import create_tables, add_user, update_user_preferences, get_user_preferences
import asyncio
import logging
import random

# Токен бота
API_TOKEN = '7531297715:AAEFnXEDYAsaHmiuVAji1YrkmvWjV781FaQ'

# Инициализация бота и базы данных
bot = Bot(token=API_TOKEN)
create_tables()  # Создание таблиц в базе данных (если их ещё нет)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

active_users = set()
user_partners = {}
searching_messages = {}  # Хранение сообщений поиска
message_mapping = {}  # Соответствие message_id между пользователями

# Обработчик команды /start
@router.message(CommandStart())
async def find_partner(message: Message):
    user_id = message.chat.id

    if user_id in user_partners:
        await message.answer("_Вы находитесь в активном диалоге.\nИспользуйте /stop чтобы закончить его._", parse_mode="Markdown")
        return

    # Отправляем сообщение о поиске
    search_message = await message.answer("_Поиск собеседника..._", parse_mode="Markdown")
    searching_messages[user_id] = search_message.message_id

    active_users.add(user_id)

    if len(active_users) > 1:
        # Ищем собеседника
        partner_id = random.choice([u for u in active_users if u != user_id])
        user_partners[user_id] = partner_id
        user_partners[partner_id] = user_id
        active_users.remove(user_id)
        active_users.remove(partner_id)

        # Удаляем сообщение о поиске
        await bot.delete_message(user_id, searching_messages[user_id])
        await bot.delete_message(partner_id, searching_messages[partner_id])
        del searching_messages[user_id]
        del searching_messages[partner_id]

        # Уведомляем пользователей
        text = (
            "_Собеседник найден_\n\n"
            "_/start — Начать диалог_\n"
            "_/stop — Прекратить диалог_\n\n"
            "_[IncognitoChatNews](https://t.me/IncognitoChatNews/7)_ • _[Community](https://t.me/incognitochat_community)_"
        )
        await bot.send_message(user_id, text, parse_mode="MarkdownV2", disable_web_page_preview=True)
        await bot.send_message(partner_id, text, parse_mode="MarkdownV2", disable_web_page_preview=True)

# Обработчик команды /stop
@router.message(Command("stop"))
async def stop_dialog(message: Message):
    user_id = message.chat.id
    partner_id = user_partners.pop(user_id, None)

    if partner_id:
        user_partners.pop(partner_id, None)

        # Уведомляем о завершении диалога
        await bot.send_message(
            user_id,
            "_Вы прекратили диалог_\n\n"
            "_/start — Начать диалог_\n"
            "_/stop — Прекратить диалог_\n\n"
            "_[IncognitoChatNews](https://t.me/IncognitoChatNews/7)_ • _[Community](https://t.me/incognitochat_community)_",
            parse_mode="MarkdownV2", disable_web_page_preview=True
        )
        await bot.send_message(
            partner_id,
            "_Собеседник прекратил диалог_\n\n"
            "_/start — Начать диалог_\n"
            "_/stop — Прекратить диалог_\n\n"
            "_[IncognitoChatNews](https://t.me/IncognitoChatNews/7)_ • _[Community](https://t.me/incognitochat_community)_",
            parse_mode="MarkdownV2", disable_web_page_preview=True
        )
    else:
        await message.answer("_Отправьте /start чтобы начать диалог._", parse_mode="Markdown")

# Обработчик команды /share
@router.message(Command("share"))
async def share_command(message: Message):
    user_id = message.chat.id
    partner_id = user_partners.get(user_id)

    if partner_id:
        user = await bot.get_chat(message.from_user.id) # Получаем информацию о пользователе
        username = user.username

        contact_link = f"[_контактом_](tg://user?id={message.from_user.id})" # Default link

        if username:
            contact_link = f"[_контактом_](https://t.me/{username})" # Link with username if available

        await bot.send_message(
            user_id,
            f"_Вы поделились своим_ {contact_link}\.",
            parse_mode="MarkdownV2",
            disable_web_page_preview=True
        )
        await bot.send_message(
            partner_id,
            f"_Собеседник поделился_ {contact_link}\.",
            parse_mode="MarkdownV2",
            disable_web_page_preview=True
        )

    else:
        await message.answer("_Отправьте /start чтобы начать диалог._", parse_mode="Markdown")

# Обработчик всех сообщений
@router.message()
async def forward_message(message: Message):
    user_id = message.chat.id
    partner_id = user_partners.get(user_id)

    if partner_id:
        try:
            if message.reply_to_message:
                replied_to_id = message.reply_to_message.message_id
                partner_replied_id = message_mapping.get((user_id, replied_to_id)) or \
                                     message_mapping.get((partner_id, replied_to_id))

                # Отправка сообщения с цитатой
                sent_message = await send_message_with_reply(message, partner_id, partner_replied_id)
            else:
                # Обычная пересылка без цитаты
                sent_message = await send_message(message, partner_id)

            # Сохраняем соответствие message_id
            message_mapping[(partner_id, sent_message.message_id)] = message.message_id

        except Exception as e:
            logging.error(f"Ошибка пересылки сообщения: {e}")
            await message.answer("**Произошла ошибка.**", parse_mode="MarkdownV2")
    else:
        await message.answer("_Отправьте /start чтобы начать диалог._", parse_mode="Markdown")

async def send_message_with_reply(message: Message, partner_id: int, reply_to_message_id: int):
    """Отправка сообщения с цитатой"""
    if message.text:
        return await bot.send_message(partner_id, message.text, reply_to_message_id=reply_to_message_id)
    elif message.photo:
        return await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption, reply_to_message_id=reply_to_message_id)
    elif message.video:
        return await bot.send_video(partner_id, message.video.file_id, caption=message.caption, reply_to_message_id=reply_to_message_id)
    elif message.document:
        return await bot.send_document(partner_id, message.document.file_id, caption=message.caption, reply_to_message_id=reply_to_message_id)
    elif message.animation:
        return await bot.send_animation(partner_id, message.animation.file_id, caption=message.caption, reply_to_message_id=reply_to_message_id)
    elif message.sticker:
        return await bot.send_sticker(partner_id, message.sticker.file_id, reply_to_message_id=reply_to_message_id)
    elif message.voice:
        return await bot.send_voice(partner_id, message.voice.file_id, reply_to_message_id=reply_to_message_id)
    elif message.video_note:
        return await bot.send_video_note(partner_id, message.video_note.file_id, reply_to_message_id=reply_to_message_id)

async def send_message(message: Message, partner_id: int):
    """Отправка обычного сообщения"""
    if message.text:
        return await bot.send_message(partner_id, message.text)
    elif message.photo:
        return await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
    elif message.video:
        return await bot.send_video(partner_id, message.video.file_id, caption=message.caption)
    elif message.document:
        return await bot.send_document(partner_id, message.document.file_id, caption=message.caption)
    elif message.animation:
        return await bot.send_animation(partner_id, message.animation.file_id, caption=message.caption)
    elif message.sticker:
        return await bot.send_sticker(partner_id, message.sticker.file_id)
    elif message.voice:
        return await bot.send_voice(partner_id, message.voice.file_id)
    elif message.video_note:
        return await bot.send_video_note(partner_id, message.video_note.file_id)

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())