import time

import ping3
from paho.mqtt import client as mqtt_client

import myhome
from myhome import logger

broker = myhome.config['monitor']['mqtt_broker']
triggered_topic = 'me/motion_sensor'
callback_topic = 'me/leave_home'


def connect_mqtt():
    client = mqtt_client.Client()
    client.username_pw_set('well-known', 'well-known')
    client.connect(broker)
    return client


def subscribe(client: mqtt_client):
    def on_message(_client, userdata, msg):
        logger.info(f'Received `{msg.payload.decode()}` from `{triggered_topic}` topic, start leave home countdown')

        for _ in range(myhome.config['monitor']['leave_home_count_down_max']):
            time.sleep(myhome.config['monitor']['interval'])
            if ping3.ping(myhome.config['monitor']['ip_addr'], timeout=1):
                logger.info('still home, stop leave home countdown')
                return

        logger.info('leave home, execute leave home commands by mqtt')
        _client.publish(callback_topic, '{"status": "absent"}')

    client.subscribe(triggered_topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
