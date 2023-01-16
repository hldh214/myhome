import asyncio

import ping3
import asyncio_mqtt

import myhome
from myhome import logger

hostname = myhome.config['monitor']['mqtt_broker']
username = 'well-known'
password = 'well-known'

triggered_topic = 'me/motion_sensor'
callback_topic = 'me/leave_home'

pd_task = None


async def presence_detection(client: asyncio_mqtt.Client):
    alive = 0
    dead = 0

    for _ in range(myhome.config['monitor']['leave_home_count_down_max']):
        await asyncio.sleep(myhome.config['monitor']['interval'])
        if ping3.ping(myhome.config['monitor']['ip_addr'], timeout=1):
            alive += 1
        else:
            dead += 1

    if alive > dead:
        logger.info(f'Still home, alive: {alive}, dead: {dead}')
        return

    logger.info(f'Leave home, execute leave home commands by mqtt, alive: {alive}, dead: {dead}')
    await client.publish(callback_topic, '{"status": "absent"}')


async def main():
    reconnect_interval = 5

    while True:
        try:
            async with asyncio_mqtt.Client(hostname=hostname, username=username, password=password) as client:
                async with client.messages() as messages:
                    await client.subscribe(triggered_topic)
                    async for message in messages:
                        logger.info(f'Received `{message.payload.decode()}` from `{triggered_topic}` topic.')

                        global pd_task
                        if pd_task is not None and not pd_task.done():
                            logger.warning('Cancel previous task due to new message received.')
                            pd_task.cancel()

                        pd_task = asyncio.create_task(presence_detection(client))
        except asyncio_mqtt.MqttError as error:
            logger.error(f'Error "{error}". Reconnecting in {reconnect_interval} seconds.')
            await asyncio.sleep(reconnect_interval)


if __name__ == '__main__':
    asyncio.run(main())
