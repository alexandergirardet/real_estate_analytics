# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import string
import json
import uuid
import requests

from google.cloud import storage
from google.oauth2 import service_account


class RealEstateExtractionPipeline:

    def __init__(self):
        self.items = []

        # self.token = self.get_access_token()

        self.bucket_name = 'rightmove_storage_dev'

        service_account_file = "../../.keys/gcp_key.json"

        credentials = service_account.Credentials.from_service_account_file(service_account_file)
        self.client = storage.Client(credentials=credentials)

    # def get_access_token(self):
    #     f = open('./access_token.txt', 'r')
    #     token_text = f.read()  
    #     token = token_text.replace('\n', '')

    #     return token

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

            self.send_items_to_bucket()

        return len(self.items)
    
    # create a function that removes punctuation from a string expect for commas
    def remove_punctuation_except_commas(self, text):
        return text.translate(str.maketrans('', '', string.punctuation.replace(',', '')))
    
    def close_spider(self, spider):

        print("SPIDER CLOSING...")

        if len(self.items) > 0:

            self.send_items_to_bucket()

    # def send_items_to_bucket(self):
    #     file_id = str(uuid.uuid4())

    #     # data = '\n'.join(json.dumps(d) for d in self.items)
    #     data = json.dumps(self.items)
        
    #     api_url = f"https://www.googleapis.com/upload/storage/v1/b/{self.bucket_name}/o?uploadType=media&name=rightmove/raw_data/{file_id}.json"
    #     headers = {
    #         "Authorization": f"Bearer {self.token}",
    #         "Content-Type": "application/json"
    #     }
    #     response = requests.post(api_url, headers=headers, data=data)
        
    #     if response.status_code == 200:
    #         print("BUCKET SUCCESSFULLY UPLOADED DATA")
    #         self.items = []
    #         return response
        
    #     else:
    #         print("BUCKET FAILED TO UPLOAD DATA")
    #         return response.text
        

    def send_items_to_bucket(self):
        file_id = str(uuid.uuid4())

        # data = '\n'.join(json.dumps(d) for d in self.items) This is to make json new line delimited
        data = json.dumps(self.items)

        bucket = self.client.get_bucket(self.bucket_name)
        blob = bucket.blob(f"rightmove/raw_data/{file_id}.json")

        try:
            blob.upload_from_string(data, content_type="application/json")
            print("BUCKET SUCCESSFULLY UPLOADED DATA")
            self.items = []
            return True
        except Exception as e:
            print(f"BUCKET FAILED TO UPLOAD DATA: {e}")
            return False
