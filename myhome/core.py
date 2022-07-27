import subprocess

from myhome import config


def run_group_command(command, logging_function=None):
    if callable(logging_function):
        logging_function(f'executing group command: {command}')
    for each_command in config.get('group')[command]['commands']:
        run_single_command(each_command)


def run_single_command(command, logging_function=None):
    if callable(logging_function):
        logging_function(f'executing single command: {command}')
    infrared = [each for each in config.get('infrared') if each['command'] == command][0]
    subprocess.call(['termux-infrared-transmit', '-f', *infrared['params']])
