import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from requests.exceptions import HTTPError
from telegram import Bot

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

bot = Bot(token=TELEGRAM_TOKEN)

# логирование
logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log', filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('bot_logger.log',
                              maxBytes=4086,
                              backupCount=2)
logger.addHandler(handler)


def parse_homework_status(homework):
    """В зависимости от статуса ф-ция формирует сообщение"""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        return logger.error('Отсутствует имя проекта')
    status = homework.get('status')
    msg = {'rejected': 'К сожалению, в работе нашлись ошибки.',
           'approved': 'Ревьюеру всё понравилось, работа зачтена!',
           'reviewing': 'Работа взята в ревью'}
    if status not in msg:
        logger.error('Неизвестный статус работы!')
    else:
        return f'У вас проверили работу "{homework_name}"!\n\n{msg[status]}'


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def get_homeworks(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    if current_timestamp is None:
        current_timestamp = int(time.time())
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(url,
                                         headers=headers,
                                         params=payload)
        return homework_statuses.json()
    except HTTPError as http_err:
        msg = f'HTTP error: {http_err}'
        send_message(msg)
        return logger.error(msg)
    except Exception as err:
        msg = f'Other error: {err}'
        send_message(msg)
        return logger.error(msg)


def main():
    current_timestamp = int(time.time())  # Начальное значение timestamp
    while True:
        try:
            logger.debug('Бот запущен')
            homeworks = get_homeworks(current_timestamp).get('homeworks')
            if len(homeworks) != 0:
                send_message(parse_homework_status(homeworks[0]))
                logger.info('Бот отправил сообщение')
            time.sleep(5 * 60)
        except Exception as e:
            msg_error = f'Бот упал с ошибкой: {e}'
            logger.error(msg_error)
            send_message(msg_error)
            time.sleep(10)


if __name__ == '__main__':
    main()
