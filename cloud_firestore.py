from datetime import date

from google.cloud import firestore


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
