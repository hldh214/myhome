import asyncio

import httpx
import ping3
import asyncio_mqtt

import myhome
from myhome import logger

hostname = myhome.config['monitor']['mqtt_broker']
username = 'well-known'
password = 'well-known'

pir_triggered_topic = 'me/motion_sensor'
leave_home_callback_topic = 'me/leave_home'
air_cleaner_control_topic = 'home/bedroom/air_cleaner/set'

pd_task = None
opener = httpx.AsyncClient()
opener.headers.update({
    'cookie': myhome.config['monitor']['cocoro']['cookie'],
})


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
    await client.publish(leave_home_callback_topic, '{"status": "absent"}')


async def pir_triggered_handler(client: asyncio_mqtt.Client, message):
    global pd_task
    if pd_task is not None and not pd_task.done():
        logger.warning('Cancel previous task due to new message received.')
        pd_task.cancel()

    pd_task = asyncio.create_task(presence_detection(client))


async def air_cleaner_control_handler(client: asyncio_mqtt.Client, message):
    json_data = {
        "deviceToken": myhome.config['monitor']['cocoro']['device_token'],
        "additional_reqest": True,
        "model_name": myhome.config['monitor']['cocoro']['model_name'],
        "event_key": "echonet_control",
    }

    if message.payload.decode() == 'ON':
        json_data.update({"data": [{"epc": "0x80", "edt": "0x30"}, {"opc": "k3", "odt": {"s6": "FF"}}]})
    elif message.payload.decode() == 'OFF':
        json_data.update({"data": [{"epc": "0x80", "edt": "0x31"}, {"opc": "k3", "odt": {"s6": "00"}}]})

    res = await opener.post('https://cocoroplusapp.jp.sharp/v1/cocoro-air/sync/air-cleaner', json=json_data)

    logger.info(f'Air cleaner control result: {res.status_code}, {res.text}')


async def main():
    reconnect_interval = 5

    while True:
        try:
            async with asyncio_mqtt.Client(hostname=hostname, username=username, password=password) as client:
                async with client.messages() as messages:
                    await client.subscribe('#')
                    async for message in messages:
                        logger.info(f'Received `{message.payload.decode()}` from `{message.topic}` topic.')

                        if message.topic.match(pir_triggered_topic):
                            await pir_triggered_handler(client, message)
                        if message.topic.match(air_cleaner_control_topic):
                            await air_cleaner_control_handler(client, message)
        except asyncio_mqtt.MqttError as error:
            logger.error(f'Error "{error}". Reconnecting in {reconnect_interval} seconds.')
            await asyncio.sleep(reconnect_interval)
        except KeyboardInterrupt:
            logger.info('Bye!')
            await opener.aclose()
            break


if __name__ == '__main__':
    asyncio.run(main())
