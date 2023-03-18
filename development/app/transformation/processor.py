import json
import datetime
import logging
import uuid

from transformer import ParquetTransformer

from google.cloud import storage

from dotenv import load_dotenv

import pandas as pd

logger = logging.getLogger(__name__)
from io import BytesIO

GCP_CREDS_PATH = "../keys/gcp-key.json"

class SilverProcessor:

    def __init__(self):
        self.bucket_name = "rightmove_storage_dev"
        self.client = storage.Client.from_service_account_json(json_credentials_path=GCP_CREDS_PATH)
        self.transformer = ParquetTransformer()

    def fetch_all_files(self, delimiter=None):
        blobs = self.client.list_blobs(self.bucket_name, prefix=f"rightmove/raw_data/", delimiter=delimiter)

        all_files = []

        for blob in blobs:
            name = blob.name
            all_files.append(name)
        return all_files
    
    def fetch_all_processed_files(self, delimiter=None):
        blobs = self.client.list_blobs(self.bucket_name, prefix=f"rightmove/processed_data/", delimiter=delimiter)

        all_files = []

        for blob in blobs:
            name = blob.name
            all_files.append(name)
        return all_files

    def download_data(self, file_name: str) -> object:
    
        bucket = self.client.bucket(self.bucket_name)
        file_path = f"rightmove/raw_data/{file_name}"
        
        blob = bucket.blob(file_path)
        
        json_string = blob.download_as_string()
        json_data = json.loads(json_string)
        
        return json_data

    def upload_data(self, data: object, file_name: str, invalid=False) -> object:
    
        bucket = self.client.bucket(self.bucket_name)
        
        if invalid:
            upload_file_path = f"rightmove/invalid_data/{file_name}"
            blob = bucket.blob(upload_file_path)
            json_data = json.dumps(data).encode('utf-8')
            blob.upload_from_string(json_data, content_type='application/json')
        else:
            parquet_file_name = file_name.replace(".json", ".snappy.parquet")
            upload_file_path = f"rightmove/processed_data/{parquet_file_name}"
            blob = bucket.blob(upload_file_path)
            blob.upload_from_string(data.to_parquet(compression='snappy'))
        
        success_flag = True

        return success_flag
    
    def get_files_to_process(self):
        files = self.fetch_all_files()
        file_names = [file.split("/")[-1] for file in files]

        processed_files = self.fetch_all_processed_files()
        processed_file_names = [file.split("/")[-1] for file in processed_files]
        processed_file_names_json = [file_name.replace(".snappy.parquet", ".json") for file_name in processed_file_names]

        unprocessed_file_names = [file for file in file_names if file not in processed_file_names_json]

        return unprocessed_file_names


    def process_data(self):
        unprocessed_file_names = self.get_files_to_process()

        print(f"Processing {len(unprocessed_file_names)} files")

        for file_name in unprocessed_file_names:
            data = self.download_data(file_name)

            valid_data, invalid_data = self.transformer.transform_data(data)
            
            if len(invalid_data):
                # invalid_df = pd.DataFrame(invalid_data)
                flag = self.upload_data(invalid_data, file_name, invalid=True)
                if flag:
                    print(f"Unsuccesfully transformed {len(invalid_data)} properties and successfully uploaded")
                else:
                    print(f"Unsuccesfully transformed {len(invalid_data)} properties and unsuccessfully uploaded")
                
            valid_df = pd.DataFrame(valid_data)
            flag = self.upload_data(valid_df, file_name, invalid=False)
            if flag:
                print(f"Successfully transformed {len(valid_data)} properties and successfully uploaded ")
            else:
                print(f"Successfully transformed {len(valid_data)} properties and unsuccessfully uploaded ")

if __name__ == "__main__":
    processor = SilverProcessor()
    processor.process_data()