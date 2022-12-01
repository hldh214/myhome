import inspect
import subprocess

from myhome import config


def get_infrared_by_command(_type, command):
    assert _type in ('single', 'group')

    result = [each for each in config['infrared'][_type] if each['command'] == command]

    assert len(result) == 1

    return result[0]


async def run_group_command(command, logging_function=None):
    group = command
    if isinstance(command, str):
        group = get_infrared_by_command('group', command)

    if callable(logging_function):
        log_message = f'executing group command: {command}'
        if inspect.iscoroutinefunction(logging_function):
            await logging_function(log_message)
        else:
            logging_function(log_message)

    for each_command in group['commands']:
        await run_single_command(each_command, logging_function)


async def run_single_command(command, logging_function=None):
    infrared = command
    if isinstance(command, str):
        infrared = get_infrared_by_command('single', command)

    if callable(logging_function):
        log_message = f'executing single command: {infrared.get("command")}'
        if inspect.iscoroutinefunction(logging_function):
            await logging_function(log_message)
        else:
            logging_function(log_message)

    subprocess.call(['termux-infrared-transmit', '-f', *infrared['params']])
