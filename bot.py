# file: bot.py
import logging
import database
import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Ваш ключ вставлен сюда
import os
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Настраиваем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Логика бота ---

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Проверка групп для отправки напоминаний...")
    groups_to_remind = database.get_groups_to_remind()
    
    if not groups_to_remind:
        logger.info("Нет групп для напоминания.")
        return

    for group_id in groups_to_remind:
        try:
            await context.bot.send_message(
                chat_id=group_id, 
                text="❗Напоминание: в этом чате давно не было сообщений!"
            )
            database.update_last_message_time(group_id, "Unknown Group")
            logger.info(f"Напоминание отправлено в группу {group_id}")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение в группу {group_id}: {e}")

# --- ОБРАБОТЧИК для команды /set_timer_minutes ---
async def set_timer_minutes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Устанавливает интервал напоминаний в минутах для текущего чата."""
    chat = update.effective_chat
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("Эту команду можно использовать только в группах.")
        return

    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите количество минут после команды. \nПример: /set_timer_minutes 5")
        return

    try:
        minutes = int(context.args[0])
        if minutes <= 0:
            await update.message.reply_text("Количество минут должно быть положительным числом.")
            return

        # Вызываем новую функцию из database.py
        database.set_group_interval_minutes(chat.id, minutes)
        await update.message.reply_text(f"Отлично! Теперь я буду присылать напоминания в этот чат, если не будет сообщений в течение {minutes} минут.")
    except (ValueError, IndexError):
        await update.message.reply_text("Неверный формат. Укажите количество минут в виде числа. \nПример: /set_timer_minutes 5")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает любое сообщение или добавление бота в группу."""
    chat = update.effective_chat
    
    if update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                logger.info(f"Бот добавлен в группу '{chat.title}' ({chat.id})")
                # Обновляем приветственное сообщение
                await context.bot.send_message(
                    chat_id=chat.id,
                    text="Привет! Я бот для напоминаний.\n\n"
                         "Чтобы настроить меня, используйте команду:\n"
                         "<b>/set_timer_minutes &lt;количество_минут&gt;</b>\n\n"
                         "Например, <code>/set_timer_minutes 10</code> установит напоминание через 10 минут тишины.",
                    parse_mode='HTML'
                )

    if chat.type in ["group", "supergroup"]:
        group_id = chat.id
        group_name = chat.title
        logger.info(f"Получено сообщение в группе '{group_name}' ({group_id}). Сбрасываю таймер.")
        database.update_last_message_time(group_id, group_name)

# --- ОСНОВНАЯ ЧАСТЬ ЗАПУСКА (С ПЛАНИРОВЩИКОМ) ---
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

async def post_init(application: Application):
    # Устанавливаем частую проверку для тестов - каждую минуту
    scheduler.add_job(send_reminders, 'interval', minutes=1, args=[application]) 
    scheduler.start()
    logger.info("Планировщик задач запущен (проверка каждую минуту).")

def main():
    database.init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # --- РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ---
    # Меняем команду на /set_timer_minutes
    application.add_handler(CommandHandler("set_timer_minutes", set_timer_minutes))
    application.add_handler(MessageHandler(filters.TEXT | filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_message))

    logger.info("Бот запускается...")
    application.run_polling()


if __name__ == "__main__":
    main()
