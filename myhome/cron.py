import time

import schedule

from myhome import config
from myhome.core import run_group_command, run_single_command


class Cron:
    def __init__(self):
        self.enabled = True

    def run(self):
        for each_schedule in config.get('schedule'):
            if each_schedule['type'] == 'group':
                schedule.every().day.at(each_schedule['time']).do(run_group_command, each_schedule['command'])
            elif each_schedule['type'] == 'single':
                schedule.every().day.at(each_schedule['time']).do(run_single_command, each_schedule['command'])

        while True:
            time.sleep(1)

            if not self.enabled:
                continue

            schedule.run_pending()

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False
