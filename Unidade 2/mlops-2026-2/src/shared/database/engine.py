import os
import pymongo

MONGO_URL = os.environ['MONGO_URL'] 
MONGO_DB = os.environ.get('MONGO_DB', 'intent_classifier')
MONGO_PRED_COLLECTION = os.environ.get('MONGO_PRED_COLLECTION', 'predictions')

client = pymongo.MongoClient(MONGO_URL)

db = client[MONGO_DB]

prediction_collection = db[MONGO_PRED_COLLECTION]

# prediction_collection.find()
# prediction_collection.find_one()
# prediction_collection.insert()
# prediction_collection.insert_one()
# prediction_collection.update()
# prediction_collection.delete()