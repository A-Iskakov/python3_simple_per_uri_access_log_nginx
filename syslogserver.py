import asyncio
import json
import socketserver
from concurrent.futures.process import ProcessPoolExecutor
from datetime import date
from time import sleep

from pymongo import MongoClient
from redis import Redis

from settings import REDIS_HOST, REDIS_PORT, REDIS_DB_NUMBER, MONGO_HOST, MONGO_PORT, SYSLOG_HOST, SYSLOG_PORT, \
    CACHE_TIMEOUT


class MongoDatabase:

    def __init__(self):
        self.mongo_client = MongoClient(MONGO_HOST, MONGO_PORT, connect=False)
        self.mongo_db = self.mongo_client['nginx_stats']
        self.mongo_collection = self.mongo_db['per_uri_access_stats']

    def write_to_db(self, dict_to_write):
        self.mongo_collection.update_one(
            {'_id': date.today().strftime("%d_%m_%y")},
            {'$inc': dict_to_write},
            upsert=True)


class RedisCache:
    def __init__(self, redis_host=REDIS_HOST, redis_port=REDIS_PORT, db_number=REDIS_DB_NUMBER):
        self.redis_client = Redis(host=redis_host, port=redis_port, db=db_number, decode_responses=True)
        self.redis_client.set_response_callback('GET', int)

    def write_to_cache(self, accessed_uri):
        """
        :type accessed_uri: str
        """

        self.redis_client.incrby(accessed_uri)

    def cache_to_dict(self):
        """

        :rtype: dict
        """
        cache_data = {}

        for key in self.redis_client.keys():
            cache_data.update({key.replace('.', '\\'): self.redis_client.get(key)})
        return cache_data

    def flush_cache(self):
        return self.redis_client.flushdb()


main_mongo = MongoDatabase()
main_cache = RedisCache()


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
        json_data = json.loads(self.request[0][json_begin_index:])

        # get uri from request
        accessed_uri = json_data['request'].split()[1]

        main_cache.write_to_cache(accessed_uri)


def syslog_server_coroutine():
    server = socketserver.UDPServer((SYSLOG_HOST, SYSLOG_PORT), SyslogUDPHandler)
    print('Syslog Server coroutine has started ')

    # handle requests until explicit shutdown(), see python docs
    server.serve_forever()


def cache_to_db_coroutine():
    print('cache-database writing service coroutine has started')
    while True:
        sleep(CACHE_TIMEOUT)
        data_from_cache = main_cache.cache_to_dict()
        if data_from_cache:
            main_cache.flush_cache()
            main_mongo.write_to_db(data_from_cache)
            # print(len(data_from_cache), 'keys has been writen')


if __name__ == "__main__":
    executor = ProcessPoolExecutor(2)
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(loop.run_in_executor(executor, syslog_server_coroutine))
    asyncio.ensure_future(loop.run_in_executor(executor, cache_to_db_coroutine))

    loop.run_forever()

