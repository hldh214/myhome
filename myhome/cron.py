import ping3
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import STATE_RUNNING

import myhome.tgbot
import myhome.core


class Cron:
    def __init__(self):
        self.presence = True
        self.scheduler = AsyncIOScheduler()
        self.presence_job = None

    def run(self):
        if myhome.config['monitor']['enabled']:
            self.presence_job = self.scheduler.add_job(
                self.back_home_cron, 'interval', seconds=myhome.config['monitor']['interval']
            )

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
            await self.back_home()
        else:
            await self.leave_home()

    async def back_home(self):
        if self.presence:
            # still at home, reschedule to `leave_home_count_down_max` interval for slower detection
            self.presence_job.reschedule('interval', seconds=myhome.config['monitor']['leave_home_count_down_max'])
            return

        # just back home, execute `on_commands`
        for each_schedule in myhome.config['monitor']['on_commands']:
            if not each_schedule['enabled']:
                continue

            if each_schedule['type'] == 'group':
                await myhome.core.run_group_command(each_schedule['command'])
            elif each_schedule['type'] == 'single':
                await myhome.core.run_single_command(each_schedule['command'])

        self.presence = True

        return

    async def leave_home(self):
        if not self.presence:
            # still not at home
            return

        # just leave home, execute `off_commands`
        for each_schedule in myhome.config['monitor']['off_commands']:
            if not each_schedule['enabled']:
                continue

            if each_schedule['type'] == 'group':
                await myhome.core.run_group_command(each_schedule['command'])
            elif each_schedule['type'] == 'single':
                await myhome.core.run_single_command(each_schedule['command'])

        # reschedule to normal interval
        self.presence_job.reschedule('interval', seconds=myhome.config['monitor']['interval'])
        self.presence = False

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
