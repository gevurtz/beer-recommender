from pymongo import MongoClient
import urllib2
from bs4 import BeautifulSoup
from django.utils.encoding import smart_str, smart_unicode
from urlparse import urlparse
import warnings
import logging
import string
warnings.filterwarnings('ignore')
logging.basicConfig(filename='mylog.log',level=logging.ERROR)



client = MongoClient()
db = client.ratebeer

def already_scraped(field, value, collection):
    return bool(collection.find_one({field : {'$in' : [value]}}, no_cursor_timeout=True))

def getPagination(html):
    page_nums = []
    soup = BeautifulSoup(html)
    for i in soup.findAll(class_ = 'ballno'):
        page_nums.append(i.text)
    if len(page_nums) > 0:
        return int(page_nums[-1])
    else:
        return 1

def scrapeAlpha():
    letters = ['0-9','a','b','c','d','e','f','g','h','i','j','k','l',
        'm','n','o','p','q','r','s','t','u','v','w','x','y','z']
    coll = db.alphapages

    for letter in letters:
        url = 'http://www.ratebeer.com/browsebrewers-{}.htm'.format(letter)
        html_l = urllib2.urlopen(url).read().decode("latin-1")
        html = smart_unicode(html_l)
        coll.insert({"url":url, "html":html})

def get_state_urls(filepath):
    with open(filepath, 'r') as f:
        return f.read().split(',')
        


def brewUrls():
    ap = db.alphapages
    coll = db.brewUrls

    for doc in ap.find():
        soup = BeautifulSoup(doc['html'])
        for a in soup.findAll('a'):
            url = smart_str(a['href'])
            if url[:9] == '/brewers/':
                u = urlparse(url)
                brewery_id = u.path.split('/')[-2]
                brewery_url = smart_unicode(
                    'http://www.ratebeer.com{}'.format(url))
                coll.insert({"brewid":brewery_id, "brewurl":brewery_url})

def brewPages():
    bp = db.brewUrls
    coll = db.brewPages
    for doc in bp.find():
        brew_id = doc['brewid']
        brew_url = smart_str(doc['brewurl'])
        try:
           html_l = urllib2.urlopen(brew_url).read().decode('latin-1')
        except urllib2.URLError, e:
           logging.error('{}{}'.format(brew_url, e))
           continue
        else:
            html = smart_unicode(html_l)
            coll.insert({"brewid":brew_id, "url":doc['brewurl'], "html":html})
            pages = getPagination(html)
            if pages > 1:
                for page in xrange(2, pages + 1):
                    p_url = brew_url + '0/{}'.format(page)
                    try:
                        html_l = urllib2.urlopen(p_url).read().decode('latin-1')
                    except urllib2.URLError, e:
                        logging.error('{}{}'.format(p_url, e))
                        continue
                    else:
                        html = smart_unicode(html_l)
                        coll.insert({
                                    "brewid":brew_id,
                                    "url":smart_unicode(p_url),
                                    "html":html
                                    })

def beerUrls():
    bp = db.brewPages
    coll = db.beerUrls

    for doc in bp.find():
        brew_id = doc['brewid']
        brew_url = doc['url']

        soup = BeautifulSoup(doc['html'])
        for a in soup.findAll('a'):
            if (a['href'][:6] == '/beer/') and \
            (a['href'][5:11] != '/rate/') and \
            (a['href'][5:13] != '/top-50/'):
                url = smart_str(a['href'])
                u = urlparse(url)
                beer_id = u.path.split('/')[-2]
                beer_url = smart_unicode(
                    'http://www.ratebeer.com{}'.format(url))
                if already_scraped('beerid', beer_id, coll) == False:
                    coll.insert({
                        'brewid':brew_id,
                        'brewurl':brew_url,
                        'beerid':beer_id,
                        'beerurl':beer_url
                        })

def reviewPages():
    bu = db.beerUrls
    coll = db.reviewPages

    for doc in bu.find(no_cursor_timeout=True):
        brew_id = doc['brewid']
        brew_url = doc['brewurl']
        beer_id = doc['beerid']
        beer_url = doc['beerurl']
        if already_scraped('beerid', beer_id, coll ) == False:
            try:
               html_l = urllib2.urlopen(smart_str(beer_url)).read().decode('latin-1')
            except:
               continue
            else:
                html = smart_unicode(html_l)
                coll.insert({
                    "brewid":brew_id,
                    "brewurl":doc['brewurl'],
                    "beerid":doc['beerid'],
                    "beerurl":doc['beerurl'],
                    "reviewurl":doc['beerurl'],
                    "html":html,
                    })
                pages = getPagination(html)
                if pages > 1:
                    for page in xrange(2, pages + 1):
                        p_url = beer_url + '1/{}'.format(page)
                        try:
                            html_l = urllib2.urlopen(smart_str(p_url)).read().decode('latin-1')
                        except:
                            continue
                        else:
                            html = smart_unicode(html_l)
                            coll.insert({
                                "brewid":brew_id,
                                "brewurl":doc['brewurl'],
                                "beerid":doc['beerid'],
                                "beerurl":doc['beerurl'],
                                "reviewurl":smart_unicode(p_url),
                                "html":html
                                        })

def reviewCount():
    soup.find('span', id='_ratingCount8').text

def getRatings(soup):
    ratings = []
    for strong in soup.findAll('strong'):
            s = strong.text.split()
            if s[0] == 'AROMA':
                rate_num = [x.split('/') for x in s[1::2]]
                num_list = []
                for i in rate_num:
                    num_list.append(i[0])
                for i in xrange(0, len(num_list)-1, 5):
                    ratings.append((tuple(num_list[i:i+5])))
    return ratings

def getUsers(soup):
    users = []
    for a in soup.findAll('a', href=True):
        if a['href'][:6] == '/user/':
            user = a.text.encode('utf8').decode('ascii', 'ignore').split('(')[0]
            userid = a['href'][6:-1]
            users.append((user, userid))
    return users

def getText(soup):
    '''
    INPUT: beautifulsoup object created from RB review page
    OUTPUT: list of review text in lowercase w/ puncuation and newlines removed'''
    textlist = []
    for i in soup.findAll('div', style="padding: 20px 10px 20px 0px; border-bottom: 1px solid #e0e0e0; line-height: 1.5;"):
        t = i.text.lower().replace('\n', ' ')
        textlist.append(''.join(s for s in t if s not in string.punctuation))
    return textlist

def getNames(soup):
    names = []
    for name in soup.findAll('span', itemprop='name'):
        names.append(name.text)
    if len(names) > 1:
        return names[0], names[1]
    else:
        return names[0], u'none'

def getAbv(soup):
    beer_data = []
    for big in soup.findAll('big', style='color: #777;'):
        beer_data.append(big.text)
    if beer_data[-1][-1] == '%':
        return beer_data[-1][:-1]
    else:
        return u'none'

def getStyle(soup):
    style = []
    for a in soup.findAll('a', href=True):
        if a['href'][:12] == '/beerstyles/':
            style.append(a.text)
    if len(style) > 0:
        return style[0]
    else:
        return u'none'

def getReviews():
    rp = db.reviewPages
    coll = db.data

    for doc in rp.find(no_cursor_timeout=True):
        try:
            soup = BeautifulSoup(doc['html'])
            beer_name, brewery_name = getNames(soup)
            style = getStyle(soup)
            users = getUsers(soup)
            ratings = getRatings(soup)
            text = getText(soup)
        except KeyboardInterrupt:
            raise
        except:
            continue
        else:
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
