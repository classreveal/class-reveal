import pymongo
import random
import json

client = pymongo.MongoClient("mongodb://localhost:27017/")
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

def fill_test_data(amount):
    for i in range(0, amount):
        add_user(i, "Name", { "1": "A", "2": "B", "3": "C", "4": "A", "5": "B", "6": "C", "7": "A", "8": "B" })

def clearDatabase():
    db.collection.delete_many({})

if __name__ == "__main__":
    fill_test_data(10)
