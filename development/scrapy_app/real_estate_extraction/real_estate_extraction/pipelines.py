# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import string
import json
import uuid
import datetime
import psycopg2

from google.cloud import storage
from google.oauth2 import service_account


class RealEstateExtractionPipeline:

    def __init__(self):
        self.items = []

        # self.token = self.get_access_token()

        self.bucket_name = 'rightmove_storage_dev'

        service_account_file = "/.keys/gcp_key.json"

        # service_account_file = "/Users/alexandergirardet/projects/estatewise/real_estate_analytics/development/scrapy_app/.keys/gcp_key.json"

        credentials = service_account.Credentials.from_service_account_file(service_account_file)
        self.client = storage.Client(credentials=credentials)

        self.conn = psycopg2.connect(
            host="postgres",
            database="rightmove",
            port=5432, 
            user='airflow', 
            password='airflow'
            )

        self.cursor = self.conn.cursor()

        now = datetime.datetime.utcnow()

        # The now instance is denominated in UTC 0 time for commonality over several time zones

        self.ymdhm = f"{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute}"
        self.now_timestamp = int(now.timestamp())

    def process_item(self, item, spider):
        ### Create a function that takes a string and removes all punctuation 
        summary = item['summary']
        feature_list = item['feature_list']
        

        if summary:
            summary = self.remove_punctuation_except_commas(summary)

        if feature_list:
            feature_list = [self.remove_punctuation_except_commas(feature) for feature in feature_list ]

        item['summary'] = summary
        item['feature_list'] = feature_list

        self.items.append(item)

        print(len(self.items))

        if len(self.items) >= 50:  # Batch size of file

            ids, file_id = self.send_items_to_bucket()

            if file_id is not None:
                try:
                    self.send_bulk_ids(ids, file_id, self.now_timestamp)
                except Exception as e:
                    print(f"BUCKET SUCCESSFULLY UPLOADED DATA, BUT FAILED TO LOAD IDS TO DB WITH: {e}")
            else:
                print("BUCKET FAILED TO UPLOAD DATA, DO NOT UPLOAD IDS TO DB")
        return len(self.items)
    
    # create a function that removes punctuation from a string expect for commas
    def remove_punctuation_except_commas(self, text):
        return text.translate(str.maketrans('', '', string.punctuation.replace(',', '')))
    
    def close_spider(self, spider):

        print("SPIDER CLOSING...")

        if len(self.items) > 0:

            self.send_items_to_bucket()

        self.conn.close()

    def send_items_to_bucket(self):
        file_id = str(uuid.uuid4())

        ids = [item["id"] for item in self.items]

        data = json.dumps(self.items)

        bucket = self.client.get_bucket(self.bucket_name)
        blob = bucket.blob(f"rightmove/raw_data/{file_id}.json")

        try:
            blob.upload_from_string(data, content_type="application/json")
            print("BUCKET SUCCESSFULLY UPLOADED DATA")
            self.items = []
            return ids, file_id
        except Exception as e:
            print(f"BUCKET FAILED TO UPLOAD DATA: {e}")
            return [], False

    def send_bulk_ids(self, id_list, file_id, now_timestamp):
        """Inserts list of ids and metadata into postgres database

        Args:
            id_list (list): list of ids to be inserted into the database
            file_id (str): file id of the file that the ids will be contained in on GCP
            now_timestamp (datetime): timestamp of when the file was uploaded to GCP
        """
        tuples_to_insert = []

        for prop_id in id_list:
            prop_tuple = (prop_id, file_id, now_timestamp, self.ymdhm)
            tuples_to_insert.append(prop_tuple)

        tuple_string = str(tuples_to_insert)

        sql_query = f"INSERT INTO rightmove_landing_zone(rightmove_id, GCS_file_id, timestamp_scraped, partition_date) VALUES {tuple_string[1:-1]}"

        self.query_sql(sql_query, self.conn)

    def query_sql(self, query, conn):

        cursor = conn.cursor()
        cursor.execute(query)

        conn.commit()
        conn.rollback()

        print("Query successful")