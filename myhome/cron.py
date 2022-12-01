import ping3
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import STATE_RUNNING

import myhome.tgbot
import myhome.core


class Cron:
    def __init__(self):
        self.at_home = True
        self.leave_home_count_down = 0
        self.leave_home_count_down_max = myhome.config['monitor']['leave_home_count_down_max']
        self.scheduler = AsyncIOScheduler()

    def run(self):
        if myhome.config['monitor']['enabled']:
            self.scheduler.add_job(self.back_home_cron, 'interval', seconds=myhome.config['monitor']['interval'])

        for each_schedule in myhome.config.get('schedule'):
            if not each_schedule['enabled']:
                continue

            if each_schedule['type'] == 'group':
                self.scheduler.add_job(
                    myhome.core.run_group_command, 'cron', (each_schedule['command'], myhome.tgbot.send_message,),
                    day_of_week=each_schedule['day_of_week'],
                    hour=each_schedule['hour'],
                    minute=each_schedule['minute']
                )
            elif each_schedule['type'] == 'single':
                self.scheduler.add_job(
                    myhome.core.run_single_command, 'cron', (each_schedule['command'], myhome.tgbot.send_message,),
                    day_of_week=each_schedule['day_of_week'],
                    hour=each_schedule['hour'],
                    minute=each_schedule['minute']
                )

        self.scheduler.start()

    async def back_home_cron(self):
        if ping3.ping(myhome.config['monitor']['ip_addr'], timeout=1):
            myhome.logger.info('back home')
            await self.back_home()
        else:
            myhome.logger.info('leave home')
            await self.leave_home()

    async def back_home(self):
        if self.at_home:
            # still at home
            return

        if self.leave_home_count_down > 0:
            self.leave_home_count_down = 0
            return

        self.at_home = True
        for each_schedule in myhome.config['monitor']['on_commands']:
            if not each_schedule['enabled']:
                continue

            if each_schedule['type'] == 'group':
                await myhome.core.run_group_command(each_schedule['command'])
            elif each_schedule['type'] == 'single':
                await myhome.core.run_single_command(each_schedule['command'])

        return

    async def leave_home(self):
        if not self.at_home:
            # still not at home
            return

        if self.leave_home_count_down < self.leave_home_count_down_max:
            self.leave_home_count_down += 1
            return

        self.at_home = False
        for each_schedule in myhome.config['monitor']['off_commands']:
            if not each_schedule['enabled']:
                continue

            if each_schedule['type'] == 'group':
                await myhome.core.run_group_command(each_schedule['command'])
            elif each_schedule['type'] == 'single':
                await myhome.core.run_single_command(each_schedule['command'])

        return

    def is_enabled(self):
        return self.scheduler.state == STATE_RUNNING

    async def enable(self, logging_function=None):
        if callable(logging_function):
            await logging_function('enabling cron')
        self.scheduler.resume()

    async def disable(self, logging_function=None):
        if callable(logging_function):
            await logging_function('disabling cron')
        self.scheduler.pause()
