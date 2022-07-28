import functools

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

from myhome import logger, config
from myhome.core import run_single_command, run_group_command
from myhome.cron import Cron

CRON_ENABLE = 'Cron disabled, Click to enable'
CRON_DISABLE = 'Cron enabled, Click to disable'

cron = Cron()


# noinspection PyUnusedLocal
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm a bot, please talk to me!")


async def infrared_base(infrared, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_single_command(infrared, functools.partial(logging_base, update=update, context=context))


async def group_base(group, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_group_command(group, functools.partial(logging_base, update=update, context=context))


# noinspection PyUnusedLocal
async def logging_base(message, update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(message)
    await update.message.reply_text(message)


# noinspection PyUnusedLocal
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Please choose:', reply_markup=build_keyboard_button())


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CRON_ENABLE:
        await cron.enable(functools.partial(logging_base, update=update, context=context))
        await update.message.reply_text(CRON_DISABLE, reply_markup=build_keyboard_button())
    elif update.message.text == CRON_DISABLE:
        await cron.disable(functools.partial(logging_base, update=update, context=context))
        await update.message.reply_text(CRON_ENABLE, reply_markup=build_keyboard_button())


def build_keyboard_button():
    buttons = [
        [KeyboardButton(CRON_DISABLE if cron.is_enabled() else CRON_ENABLE)],
        [KeyboardButton(f"/{each_group['command']}") for each_group in config.get('group')]
    ]

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


# noinspection PyTypeChecker
def main():
    application = ApplicationBuilder().token(config.get('token')).build()

    application.add_handler(CommandHandler('start', start_handler, filters.User(username=config.get('username'))))
    application.add_handler(CommandHandler('menu', menu_handler, filters.User(username=config.get('username'))))

    for each_infrared in config.get('infrared'):
        application.add_handler(CommandHandler(
            each_infrared['command'],
            functools.partial(infrared_base, each_infrared),
            filters.User(username=config.get('username'))
        ))

    for each_group in config.get('group'):
        application.add_handler(CommandHandler(
            each_group['command'],
            functools.partial(group_base, each_group),
            filters.User(username=config.get('username'))
        ))

    logger.info('starting cron thread')
    cron.run()

    application.add_handler(MessageHandler(
        filters.User(username=config.get('username')) & filters.Text(),
        message_handler
    ))

    application.run_polling()
