import pymongo
import json
import os

ip = os.environ.get("MONGO_IP")
username = os.environ.get("MONGO_USERNAME")
password = os.environ.get("MONGO_PASSWORD")
auth_database = os.environ.get("MONGO_AUTH_DATABASE")

client = pymongo.MongoClient(f"mongodb://{username}:{password}@{ip}/?authSource={auth_database}")
db = client["class-reveal"]
collection = db.users

def add_user(user_id, name, hits, schedule):
    post = {
        "user_id": str(user_id),
        "name": str(name),
        "hits": hits,
        "schedule": schedule
    }

    collection.delete_many({"user_id": str(user_id)})
    collection.insert_one(post)

def get_user(user_id):
    user = collection.find_one({"user_id": str(user_id)}, sort=[( '_id', pymongo.DESCENDING )])
    return user

def get_class(period, teacher_name):
    query = f"schedule.{period}.teacher_name"
    classmates = collection.find({query: teacher_name})
    return classmates

