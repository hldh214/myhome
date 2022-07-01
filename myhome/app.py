import functools
import subprocess

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from myhome import logger, get_config


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def infrared_base(command, params, update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f'executing infrared command: {command}')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'executing infrared command: {command}')
    subprocess.call(['termux-infrared-transmit', '-f', *params])


def main():
    config = get_config()

    application = ApplicationBuilder().token(config.get('token')).build()

    application.add_handler(CommandHandler('start', start))

    infrared = config.get('infrared')
    for each in infrared:
        application.add_handler(CommandHandler(
            each['command'],
            functools.partial(infrared_base, each['command'], each['params'])
        ))

    application.run_polling()
