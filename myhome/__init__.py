import json
import logging.handlers
import pathlib
import sys

from loguru import logger

project_root = pathlib.Path(__file__).parent.parent


def get_config(path='config.json'):
    with open(project_root.joinpath(path)) as f:
        return json.load(f)


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_channel = logging.handlers.TimedRotatingFileHandler(
    project_root.joinpath('builtin_logger.log'),
    interval=1,
    when='D',
    backupCount=1,
)
file_channel.setFormatter(formatter)

logger.remove()
logger.add(project_root.joinpath('loguru.log'), rotation='1 day', retention=2)
logger.add(sys.stdout, colorize=True)
