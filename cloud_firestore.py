from datetime import date

from google.cloud import firestore
from google.cloud.monitoring_v3 import MetricServiceClient
from google.cloud.monitoring_v3.query import Query


class FirestoreData:
    def __init__(self):
        self.db = firestore.Client.from_service_account_json('firestore.json')
        self.doc_ref = self.db.collection('statistics').document('common_stats')

    def get_data_from_firestore(self):
        today = date.today()
        year = str(today.year)
        month = str(today.month)
        day = str(today.day)

        main_dict = self.doc_ref.get().to_dict()

        if not main_dict:
            result = False
        elif year not in main_dict:
            result = False
        elif month not in main_dict[year]:
            result = False
        elif day not in main_dict[year][month]:
            result = False
        else:
            result = main_dict[year][month][day]
            if 'company_session_duration' in result:
                result.update(
                    {'company_session_duration': f'{round(result["company_session_duration"] / 60000, 1)} mins'})
            if 'employee_session_duration' in result:
                result.update(
                    {'employee_session_duration': f'{round(result["employee_session_duration"] / 60000, 1)} mins'})
        return result


class FireStoreStats:
    def __init__(self):
        self.client = MetricServiceClient.from_service_account_json('mploy-eur-firebase.json')

    def get_stats_from_firestore(self):
        count = 0
        for item in Query(self.client,
                          'mploy-eur',
                          'firestore.googleapis.com/document/write_count',
                          hours=24
                          ).align('ALIGN_SUM', hours=24).iter():
            count += item.points[0].value.int64_value

        return count
