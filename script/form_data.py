from pymongo import MongoClient
from bs4 import BeautifulSoup


def getReviews():
    rp = db.reviewPages
    coll = db.data

    for doc in rp.find(no_cursor_timeout=True):
        soup = BeautifulSoup(doc['html'])       
        beer_name, brewery_name = getNames(soup)
        style = getStyle(soup)
        users = getUsers(soup)
        ratings = getRatings(soup)
        text = getText(soup)
        
        for i, rating in enumerate(ratings):
            coll.insert({
                    'brewid': doc['brewid'],
                    'brewurl': doc['brewurl'],
                    'beerid' : doc['beerid'],
                    'beerurl' : doc['beerurl'],
                    'beername' : beer_name,
                    'breweryname' : brewery_name,
                    'style' : style,
                    'username' : users[i][0],
                    'userid' : users[i][1],
                    'aroma' : rating[0],
                    'appearance' : rating[1],
                    'taste' : rating[2],
                    'palate' : rating[3],
                    'overall' : rating[4],
                    'text' : text[i]
                })

if __name__ == '__main__':
    getReviews()