from datetime import date

from pymongo import MongoClient

from settings import MONGO_HOST, MONGO_PORT


class MongoDatabase:

    def __init__(self):
        self.mongo_client = MongoClient(MONGO_HOST, MONGO_PORT, connect=False)
        self.mongo_db = self.mongo_client['nginx_stats']
        self.stats_collection = self.mongo_db['per_uri_access_stats']
        self.telegram_bot_collection = self.mongo_db['telegram_bot_data']

    def write_cache_to_db(self, dict_to_write):
        self.stats_collection.update_one(
            {'_id': date.today().strftime("%d_%m_%y")},
            {'$inc': dict_to_write},
            upsert=True)

    def write_telegram_user_to_db(self, telegram_user_id):
        """

        :type telegram_user_id: int
        """
        self.telegram_bot_collection.update_one(
            {'_id': 'telegram_users'},
            {'$addToSet': {'ids': telegram_user_id}},
            upsert=True
        )

    def get_stat_data_from_db(self, query_filter):
        """

        :rtype: dict
        """
        return self.stats_collection.find_one(
            {'_id': query_filter})

    def get_telegram_data_from_db(self):
        """

        :rtype: dict
        """
        return self.telegram_bot_collection.find_one(
            {'_id': 'telegram_users'})


MAIN_MONGO = MongoDatabase()
