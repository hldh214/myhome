import functools
import subprocess

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from myhome import logger, get_config

config = get_config()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def infrared_base(command, params, update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f'executing infrared command: {command}')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'executing infrared command: {command}')
    subprocess.call(['termux-infrared-transmit', '-f', *params])


async def group_base(command, commands, update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f'executing group command: {command}')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'executing group command: {command}')

    for each_command in commands:
        infrared = [each for each in config.get('infrared') if each['command'] == each_command][0]
        await infrared_base(infrared['command'], infrared['params'], update, context)


def main():
    application = ApplicationBuilder().token(config.get('token')).build()

    application.add_handler(CommandHandler('start', start))

    for each_infrared in config.get('infrared'):
        application.add_handler(CommandHandler(
            each_infrared['command'],
            functools.partial(infrared_base, each_infrared['command'], each_infrared['params'])
        ))

    for each in config.get('group'):
        application.add_handler(CommandHandler(
            each['command'],
            functools.partial(group_base, each['command'], each['commands'])
        ))

    application.run_polling()
