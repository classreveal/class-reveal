import pymongo
import random
import json

client = pymongo.MongoClient("mongodb://mongo:27017/")
db = client.class_reveal
collection = db.users

def add_user(user_id, name, schedule):
    post = {
        "user_id": str(user_id),
        "name": str(name),
        "schedule": schedule
    }

    collection.insert_one(post)

def get_user(user_id):
    user = collection.find_one({"user_id": str(user_id)}, sort=[( '_id', pymongo.DESCENDING )])
    return user
