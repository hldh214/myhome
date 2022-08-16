import json
import pathlib
import sys

from telegram.ext import ApplicationBuilder

from loguru import logger

project_root = pathlib.Path(__file__).parent.parent


def get_config(path='config.json'):
    with open(project_root.joinpath(path)) as f:
        return json.load(f)


config = get_config()

application = ApplicationBuilder().token(config.get('token')).concurrent_updates(True).build()

logger.remove()
logger.add(project_root.joinpath('loguru.log'))
logger.add(sys.stdout, colorize=True)
