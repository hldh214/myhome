import httpx

from myhome import config, logger


def send_message(text):
    logger.info(text)

    return httpx.post(
        f'https://api.telegram.org/bot{config.get("token")}/sendMessage',
        params={'chat_id': config.get('chat_id'), 'text': text}
    )
