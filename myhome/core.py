import inspect
import subprocess

from myhome import config


async def run_group_command(group, logging_function=None):
    if callable(logging_function):
        log_message = f'executing group command: {group.get("command")}'
        if inspect.isawaitable(logging_function):
            await logging_function(log_message)
        else:
            logging_function(log_message)

    for each_command in group['commands']:
        infrared = [each for each in config.get('infrared') if each['command'] == each_command][0]
        await run_single_command(infrared, logging_function)


async def run_single_command(infrared, logging_function=None):
    if callable(logging_function):
        log_message = f'executing single command: {infrared.get("command")}'
        if inspect.isawaitable(logging_function):
            await logging_function(log_message)
        else:
            logging_function(log_message)

    subprocess.call(['termux-infrared-transmit', '-f', *infrared['params']])
