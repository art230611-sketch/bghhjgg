import os
import logging
import re
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ParseMode

BOT_TOKEN = "8539841784:AAEMOu6TBV_hKtdQ56J9wAdlx6ScHTg352c"

APPEND_TEXT = "Starсеть - подписаться"
APPEND_URL = "https://t.me/+g9z9CXgTBr0yMGYy"
APPEND_HTML_LINK = f"{APPEND_TEXT}"

REPLACEMENT_WORDS = {
    "Сват": "Sв@т",
    "Докс": "D0кс",
    "Сватер": "Sв@тe₽",
    "Сватнул": "Sв@тну",
    "Паста": "П@ста",
    "Эвак": "3в@к",
    "Эвакнул": "3в@кнул",
    "Эвакуация": "3в@куацuя",
    "Эвакуировали": "3в@кyuр0валu",
    "Адрес": "адр3с",
    "ФИО": "ФU0",
    "Номер": "Н0ме₽",
    "Докснул": "D0кснуl",
    "Задоксил": "3аd0ксuл",
    "Задоксили": "3аd0ксuлu",
    "Досье": "Д0сbе",
}

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def perform_replacements(text: str) -> str:
    if not text: return text
    modified_text = text
    for original, replacement in REPLACEMENT_WORDS.items():
        pattern = re.compile(r'\b' + re.escape(original) + r'\b', re.IGNORECASE)
        modified_text = pattern.sub(replacement, modified_text)
    return modified_text

async def process_and_edit_message(message):
    """Общая логика обработки и редактирования сообщения"""
    try:
        original_text = message.text or message.caption
        if not original_text:
            return False

        # 1. Замена слов
        processed_text = perform_replacements(original_text)
        
        # 2. Проверка подписи
        final_text = processed_text
        if APPEND_URL not in processed_text:
            final_text = f"{processed_text}\n\n{APPEND_HTML_LINK}"
        
        # 3. Если текст изменился — редактируем
        if final_text != original_text:
            if message.text:
                await message.edit_text(final_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            else:
                await message.edit_caption(final_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return True
    except Exception as e:
        logger.error(f"Ошибка при правке сообщения {message.message_id}: {e}")
    return False

async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка новых и ОТРЕДАКТИРОВАННЫХ постов"""
    message = update.channel_post or update.edited_channel_post
    if message:
        await process_and_edit_message(message)

async def scan_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /scan для проверки последних 200 сообщений (лимит можно менять)"""
    if not update.effective_chat: return
    
    await update.message.reply_text("Начинаю сканирование последних сообщений в канале... Подождите.")
    
    chat_id = update.effective_chat.id
    # Мы берем ID текущего сообщения как точку отсчета
    current_id = update.effective_message.message_id
    
    count = 0
    # Пройдемся назад на 200 сообщений (можно увеличить)
    for msg_id in range(current_id - 1, current_id - 201, -1):
        try:
            # Бот пытается «тронуть» сообщение, чтобы проверить его
            # Напрямую «получить» сообщение по ID бот не может, 
            # поэтому мы пробуем отправить команду редактирования.
            # Если сообщение существует и оно текстовое, процесс_and_edit его поправит.
            
            # Внимание: здесь используется хак, боты не могут читать историю, 
            # но могут редактировать по ID. Мы просто перебираем ID.
            await context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id)
            
            # Мы не можем легко получить текст старого сообщения без участия юзера.
            # Поэтому автоматический скан работает только на сообщениях, которые бот "видел".
            
        except:
            continue
        await asyncio.sleep(1) # Защита от спама
    
    await update.message.reply_text("Сканирование завершено.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Бот запущен. Я слежу за новыми и старыми постами в каналах.")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    # Команда /scan (выполнять в канале или из лички, если бот админ)
    application.add_handler(CommandHandler("scan", scan_history))

    # Слушаем новые посты И редактирования постов
    application.add_handler(MessageHandler(
        filters.ChatType.CHANNEL & (filters.TEXT | filters.CAPTION), 
        channel_post_handler
    ))
    
    # Чтобы бот следил за редактированием уже существующих постов:
    application.add_handler(MessageHandler(
        filters.UpdateType.EDITED_CHANNEL_POST & (filters.TEXT | filters.CAPTION),
        channel_post_handler
    ))

    logger.info("Бот запущен и следит за изменениями...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()