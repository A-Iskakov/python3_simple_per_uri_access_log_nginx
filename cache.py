from redis import Redis

from settings import REDIS_HOST, REDIS_PORT, REDIS_DB_NUMBER


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


MAIN_CACHE = RedisCache()
