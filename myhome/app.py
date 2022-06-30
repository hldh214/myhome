from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from myhome import logger, get_config


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def main():
    config = get_config()

    application = ApplicationBuilder().token(config.get('token')).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.run_polling()
