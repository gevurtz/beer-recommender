from pymongo import MongoClient

client = MongoClient()
db = client.ratebeer

def remove_dups():
    coll = db.beerUrls
    newcoll = db.noDups

    for doc in coll.find():
        beer_id = doc['beerid']
        if bool(newcoll.find_one({'beerid' : {'$in' : [beer_id]}})) == False:
            newcoll.insert(doc)

remove_dups()