from apscheduler.schedulers.asyncio import AsyncIOScheduler

from myhome import config, logger
from myhome.core import run_group_command, run_single_command


class Cron:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    def run(self):
        for each_schedule in config.get('schedule'):
            if each_schedule['type'] == 'group':
                group = [each for each in config.get('group') if each['command'] == each_schedule['command']][0]
                self.scheduler.add_job(
                    run_group_command, 'cron', (group, logger.info,),
                    day_of_week=each_schedule['day_of_week'],
                    hour=each_schedule['hour'],
                    minute=each_schedule['minute']
                )
            elif each_schedule['type'] == 'single':
                infrared = [each for each in config.get('infrared') if each['command'] == each_schedule['command']][0]
                self.scheduler.add_job(
                    run_single_command, 'cron', (infrared, logger.info,),
                    day_of_week=each_schedule['day_of_week'],
                    hour=each_schedule['hour'],
                    minute=each_schedule['minute']
                )

    async def enable(self, logging_function=None):
        if callable(logging_function):
            await logging_function('enabling cron')
        self.scheduler.resume()

    async def disable(self, logging_function=None):
        if callable(logging_function):
            await logging_function('disabling cron')
        self.scheduler.pause()
