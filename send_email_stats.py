import smtplib
from datetime import date, timedelta
from email.mime.text import MIMEText
from heapq import nlargest

from pymongo import MongoClient

from settings import MONGO_HOST, MONGO_PORT, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, \
    DEFAULT_FROM_EMAIL, ADMIN_EMAILS, TOP_MOST_ACCESSED_URIS


class MongoDatabase:

    def __init__(self):
        self.mongo_client = MongoClient(MONGO_HOST, MONGO_PORT, connect=False)
        self.mongo_db = self.mongo_client['nginx_stats']
        self.mongo_collection = self.mongo_db['per_uri_access_stats']

    def get_data_from_db(self, filter):
        """

        :rtype: dict
        """
        return self.mongo_collection.find_one(
            {'_id': filter})


if __name__ == "__main__":
    my_mongo = MongoDatabase()
    today = date.today()
    data = my_mongo.get_data_from_db(today.strftime("%d_%m_%y"))
    to_send = False
    text_message = ''
    if data is not None:
        to_send = True
        data.pop('_id')
        text_message += f'Here is top opened URI for today {today.strftime("%d_%m_%y")}\n'
        for index in nlargest(TOP_MOST_ACCESSED_URIS, data, key=data.get):
            text_message += f'URI - {index} were accessed {data.get(index)} times\n'

    today = today - timedelta(1)
    data = my_mongo.get_data_from_db(today.strftime("%d_%m_%y"))
    if data is not None:
        to_send = True
        data.pop('_id')
        text_message += f'Here is top opened URI for yesterday {today.strftime("%d_%m_%y")}\n'
        for index in nlargest(TOP_MOST_ACCESSED_URIS, data, key=data.get):
            text_message += f'URI - {index} were accessed {data.get(index)} times\n'

    if to_send:
        msg = MIMEText(text_message)
        msg['Subject'] = "Daily statistics from nginx"
        s = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
        s.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        s.sendmail(DEFAULT_FROM_EMAIL, ADMIN_EMAILS, msg.as_string())
        print('message sent')
        s.quit()
