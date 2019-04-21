import asyncio
import json
import socketserver
from concurrent.futures.process import ProcessPoolExecutor
from datetime import time
from sys import stdout
from time import sleep

from telegram.ext import Updater, CommandHandler

from cache import MAIN_CACHE
from database import MAIN_MONGO
from settings import SYSLOG_HOST, SYSLOG_PORT, \
    CACHE_TIMEOUT, TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USE_WEBHOOK, TELEGRAM_BOT_EXTERNAL_URL
from telegram_bot import send_stats_on_schedule, start, send_statistics, auth_command


# https://docs.python.org/3/library/socketserver.html
class SyslogUDPHandler(socketserver.BaseRequestHandler):
    """
    Decodes syslog data to dict.

    This class takes the recieved syslog entries and writes them to the cache.
    """

    def handle(self):
        # get index where JSON body starts
        json_begin_index = self.request[0].find(b'{')

        # format binary to JSON
        json_data = json.loads(self.request[0][json_begin_index:].encode('utf-8').strip())

        # get uri from request
        accessed_uri = json_data['request'].split()[1]

        MAIN_CACHE.write_to_cache(accessed_uri)


def syslog_server_coroutine():
    server = socketserver.UDPServer((SYSLOG_HOST, SYSLOG_PORT), SyslogUDPHandler)

    stdout.write('Syslog Server coroutine has started\n')

    # handle requests until explicit shutdown(), see python docs
    server.serve_forever()


def cache_to_db_coroutine():
    stdout.write('cache-database writing service coroutine has started\n')
    while True:
        sleep(CACHE_TIMEOUT)
        data_from_cache = MAIN_CACHE.cache_to_dict()
        if data_from_cache:
            MAIN_CACHE.flush_cache()
            MAIN_MONGO.write_cache_to_db(data_from_cache)
            # print(len(data_from_cache), 'keys has been writen')


def telegram_bot_coroutine():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    job_queue = updater.job_queue

    # job_minute = job_queue.run_repeating(callback_minute, interval=60, first=0)
    job_queue.run_daily(send_stats_on_schedule, time(23, 55))
    # add handlers

    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start, pass_args=True)
    dispatcher.add_handler(start_handler)

    auth_handler = CommandHandler('auth', auth_command, pass_args=True)
    dispatcher.add_handler(auth_handler)

    send_stats_handler = CommandHandler('stats', send_statistics)
    dispatcher.add_handler(send_stats_handler)

    if TELEGRAM_BOT_USE_WEBHOOK:
        # set up webhook
        updater.start_webhook(listen='127.0.0.1', port=8001, url_path=TELEGRAM_BOT_TOKEN)
        updater.bot.set_webhook(url=f'{TELEGRAM_BOT_EXTERNAL_URL}/{TELEGRAM_BOT_TOKEN}')
    else:
        # if webhook couldn't be set up
        updater.start_polling()

    stdout.write(f'Telegram bot coroutine has started\n{updater.bot.get_me()}\n')
    updater.idle()


if __name__ == "__main__":
    executor = ProcessPoolExecutor(3)
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(loop.run_in_executor(executor, syslog_server_coroutine))
    asyncio.ensure_future(loop.run_in_executor(executor, cache_to_db_coroutine))
    asyncio.ensure_future(loop.run_in_executor(executor, telegram_bot_coroutine))

    loop.run_forever()
