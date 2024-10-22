import pymongo
from boto3_toolkit import Boto3Utils

class MongoUtils:
    def __init__(self):
        self.config = Boto3Utils().get_secret(secret_name="GarminSleepStatisticsSecrets")
        self.client = self.connect_to_mongo()

    def connect_to_mongo(self):
        client = pymongo.MongoClient(self.config['MONGODB_CONNECTION_STRING'])
        return client[self.config['MONGODB_DATABASE']]

    def insert_records(self, collection_name, data, many = False):
        collection = self.client[collection_name]
        if not many:
            result = collection.insert_one(data)
        elif many:
            result = collection.insert_many(data)
        return result.inserted_id

    def find_one(self, collection_name, query):
        collection = self.client[collection_name]
        result = collection.find_one(query)
        return result
        
    def update_record(self, collection_name, query, update_data, upsert):
        collection = self.client[collection_name]
        result = collection.update_one(query, {'$set': update_data}, upsert = upsert)
        print(f"Updated {result.modified_count} Records Successfully")
        return result.modified_count
        
    def replace_one(self, collection_name, query, upsert = True):
        collection = self.client[collection_name]
        result = collection.replace_one(query, upsert = upsert)
        return result.modified_count