import asyncio
import functools

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from myhome import logger, config
from myhome.core import run_single_command, run_group_command
from myhome.cron import Cron


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def infrared_base(infrared, update: Update, context: ContextTypes.DEFAULT_TYPE):
    run_single_command(infrared, functools.partial(logging_base, update=update, context=context))


def group_base(group, update: Update, context: ContextTypes.DEFAULT_TYPE):
    run_group_command(group, functools.partial(logging_base, update=update, context=context))


def logging_base(message, update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(message)
    asyncio.run(context.bot.send_message(chat_id=update.effective_chat.id, text=message))


def main():
    application = ApplicationBuilder().token(config.get('token')).build()

    application.add_handler(CommandHandler('start', start))

    for each_infrared in config.get('infrared'):
        application.add_handler(CommandHandler(
            each_infrared['command'], functools.partial(infrared_base, each_infrared)
        ))

    for each in config.get('group'):
        application.add_handler(CommandHandler(
            each['command'], functools.partial(group_base, each)
        ))

    cron = Cron()
    logger.info('starting cron thread')
    cron.run()
    application.add_handler(CommandHandler('cron_enable', lambda update, context: cron.enable(
        functools.partial(logging_base, update=update, context=context))))
    application.add_handler(CommandHandler('cron_disable', lambda update, context: cron.disable(
        functools.partial(logging_base, update=update, context=context))))

    application.run_polling()
