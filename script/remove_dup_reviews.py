from pymongo import MongoClient

client = MongoClient()
db = client.ratebeer

def remove_dups():
    coll = db.reviewPages
    newcoll = db.reviewnd

    for doc in coll.find(no_cursor_timeout=True):
        r_url = doc['reviewurl']
        if bool(newcoll.find_one({'reviewurl' : {'$in' : [r_url]}})) == False:
            newcoll.insert(doc)