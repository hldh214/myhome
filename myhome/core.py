import subprocess

from myhome import config


def run_group_command(group, logging_function=None):
    if callable(logging_function):
        logging_function(f'executing group command: {group.get("command")}')
    for each_command in group['commands']:
        infrared = [each for each in config.get('infrared') if each['command'] == each_command][0]
        run_single_command(infrared, logging_function)


def run_single_command(infrared, logging_function=None):
    if callable(logging_function):
        logging_function(f'executing single command: {infrared.get("command")}')
    subprocess.call(['termux-infrared-transmit', '-f', *infrared['params']])
