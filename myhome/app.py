import functools
import threading

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from myhome import logger, config
from myhome.core import run_single_command, run_group_command
from myhome.cron import Cron


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def infrared_base(command, update: Update, context: ContextTypes.DEFAULT_TYPE):
    run_single_command(command, functools.partial(logging_base, update=update, context=context))


async def group_base(command, update: Update, context: ContextTypes.DEFAULT_TYPE):
    run_group_command(command, functools.partial(logging_base, update=update, context=context))


async def logging_base(message, update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(message)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def main():
    application = ApplicationBuilder().token(config.get('token')).build()

    application.add_handler(CommandHandler('start', start))

    for each_infrared in config.get('infrared'):
        application.add_handler(CommandHandler(
            each_infrared['command'],
            lambda update, context: infrared_base(each_infrared['command'], update, context)
        ))

    for each in config.get('group'):
        application.add_handler(CommandHandler(
            each['command'],
            lambda update, context: group_base(each['command'], update, context)
        ))

    cron = Cron()
    logger.info('starting cron thread')
    threading.Thread(target=cron.run()).start()
    application.add_handler(CommandHandler('cron_enable', lambda update, context: cron.enable()))
    application.add_handler(CommandHandler('cron_disable', lambda update, context: cron.disable()))

    application.run_polling()
