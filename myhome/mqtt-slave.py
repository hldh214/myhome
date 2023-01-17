import asyncio
import json

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
air_cleaner_state_topic = 'home/bedroom/air_cleaner'

pd_task = None


# Credit: https://github.com/rcmdnk/cocoro
class Cocoro():
    def __init__(self, app_secret, terminal_app_id_key, _logger):
        self.app_secret = app_secret
        self.terminal_app_id_key = terminal_app_id_key
        self.logger = _logger

        self.config = {'name': None}

        self.url_prefix = 'https://hms.cloudlabs.sharp.co.jp/hems/pfApi/ta'
        self.headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': '*/*',
            'User-Agent': 'smartlink_v200i Mozilla/5.0 '
                          '(iPhone; CPU iPhone OS 14_4 like Mac OS X) '
                          'AppleWebKit/605.1.15 (KHTML, like Gecko) '
                          'Mobile/15E148',
            'Accept-Language': 'ja-jp',
            'Connection': 'keep-alive',
            'Proxy-Connection': 'keep-alive',
        }

        self.control = {
            'switch': {
                'on': (
                    '30',
                    '00030000000000000000000000FF00000000000000000000000000'),
                'off': (
                    '31',
                    '000300000000000000000000000000000000000000000000000000')},
            'humidification': {
                'on': (
                    None,
                    '000900000000000000000000000000FF0000000000000000000000'),
                'off': (
                    None,
                    '000900000000000000000000000000000000000000000000000000')},
            'mode': {
                'auto': (
                    None,
                    '010100001000000000000000000000000000000000000000000000'),
                'sleep': (
                    None,
                    '010100001100000000000000000000000000000000000000000000'),
                'pollen': (
                    None,
                    '010100001300000000000000000000000000000000000000000000'),
                'quiet': (
                    None,
                    '010100001400000000000000000000000000000000000000000000'),
                'medium': (
                    None,
                    '010100001500000000000000000000000000000000000000000000'),
                'high': (
                    None,
                    '010100001600000000000000000000000000000000000000000000'),
                'recommendation': (
                    None,
                    '010100002000000000000000000000000000000000000000000000'),
                'effective': (
                    None,
                    '010100004000000000000000000000000000000000000000000000')}}

    def get_headers(self, **kw):
        headers = self.headers.copy()
        for k, v in kw.items():
            headers[k] = v
        return headers

    def get_cookies(self):
        if 'cookies' in self.config:
            return self.config['cookies']
        url = self.url_prefix + '/setting/login/'
        headers = self.get_headers()
        params = (
            ('appSecret', self.app_secret),
            ('serviceName', 'iClub'),
        )
        data = {'terminalAppId': f'https://db.cloudlabs.sharp.co.jp/clpf/key/{self.terminal_app_id_key}'}
        data = json.dumps(data).replace('/', '\\/')
        response = httpx.post(url, headers=headers, params=params, data=data)
        if response.status_code != 200 or 'JSESSIONID' not in response.cookies:
            self.logger.error('Failed to get cookie')
            return False
        self.config['cookies'] = {'JSESSIONID': response.cookies['JSESSIONID']}
        return self.config['cookies']

    def get_box_par(self):
        for box in self.config['box']:
            for echonetData in box['echonetData']:
                name = echonetData['labelData']['name'].strip('"\'')
                if (self.config['name'] is None
                    or name
                    == self.config['name']):
                    self.config['boxId'] = box['boxId']
                    self.config['echonetData'] = echonetData
                    self.config['name'] = name
                    return True
        if self.config['name'] is None:
            self.logger.error('Could not find any device')
            return False
        self.config['boxId'] = self.config['box'][0]['boxId']
        self.config['echonetData'] = self.config['box'][0]['echonetData'][0]
        self.logger.warning(
            f'Could not find device named {self.config["name"]}. '
            'Use the first device: '
            f'{self.config["echonetData"]["labelData"]["name"]}.')
        return True

    def get_box(self):
        if 'box' in self.config:
            return True
        url = self.url_prefix + '/setting/boxInfo/'
        headers = self.get_headers()
        cookies = self.get_cookies()
        if not cookies:
            return False
        params = (
            ('appSecret', self.app_secret),
            ('mode', 'other'),
        )
        response = httpx.get(url, headers=headers, params=params,
                             cookies=cookies)
        if response.status_code != 200:
            self.logger.error('Failed to get box information')
            return False
        self.config.update(response.json())
        if not self.get_box_par():
            return False
        return True

    def device_control(self, system, target):
        if not self.get_box():
            return False
        url = self.url_prefix + '/control/deviceControl'
        headers = self.get_headers(**{'Connection': 'close', 'Proxy-Connection': 'close'})
        cookies = self.get_cookies()
        if not cookies:
            return False
        params = (
            ('appSecret', self.app_secret),
            ('boxId', self.config['boxId']),
        )
        data = {
            'controlList': [{
                'status': [{
                    'valueBinary': {'code': self.control[system][target][1]},
                    'statusCode': 'F3',
                    'valueType': 'valueBinary'
                }],
                'deviceId': self.config['echonetData']['deviceId'],
                'echonetNode': self.config['echonetData']['echonetNode'],
                'echonetObject': self.config['echonetData']['echonetObject']
            }]
        }
        if self.control[system][target][0] is not None:
            data['controlList'][0]['status'].append(
                {
                    'valueSingle': {'code': self.control[system][target][0]},
                    'statusCode': '80',
                    'valueType': 'valueSingle'
                })
        data = json.dumps(data)
        response = httpx.post(url, headers=headers, params=params,
                              cookies=cookies, data=data)
        if response.status_code != 200:
            self.logger.error(f'Failed to control {self.config["name"]}: '
                              f'{system} {target}. '
                              f'Status code: {response.status_code}.')
            return False
        data = response.json()
        if data['controlList'][0]['errorCode'] is not None:
            self.logger.error(f'Failed to control: {self.config["name"]} '
                              f'{system} {target}')
            return False
        return True

    def device_info(self, key='labelData'):
        if not self.get_box():
            return False
        if key == 'full':
            return self.config['echonetData']
        if key in self.config['echonetData'].keys():
            return self.config['echonetData'][key]
        if key in self.config['echonetData']['labelData'].keys():
            return self.config['echonetData']['labelData'][key]
        self.logger.warning('Invalid key for device_info()')
        return False


cocoro = Cocoro(
    myhome.config['monitor']['cocoro']['app_secret'],
    myhome.config['monitor']['cocoro']['terminal_app_id_key'],
    logger
)


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
    if message.payload.decode() == 'ON':
        if cocoro.device_control('switch', 'on'):
            await client.publish(air_cleaner_state_topic, 'ON', retain=True)
    elif message.payload.decode() == 'OFF':
        if cocoro.device_control('switch', 'off'):
            await client.publish(air_cleaner_state_topic, 'OFF', retain=True)


async def main():
    reconnect_interval = 5

    while True:
        try:
            async with asyncio_mqtt.Client(hostname=hostname, username=username, password=password) as client:
                async with client.messages() as messages:
                    await client.subscribe('#')
                    async for message in messages:
                        logger.info(f'Received `{message.payload.decode()}` from `{message.topic}` topic.')

                        if message.topic.matches(pir_triggered_topic):
                            await pir_triggered_handler(client, message)
                        if message.topic.matches(air_cleaner_control_topic):
                            await air_cleaner_control_handler(client, message)
        except asyncio_mqtt.MqttError as error:
            logger.error(f'Error "{error}". Reconnecting in {reconnect_interval} seconds.')
            await asyncio.sleep(reconnect_interval)


if __name__ == '__main__':
    asyncio.run(main())
