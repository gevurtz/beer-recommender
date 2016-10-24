import urllib2
from bs4 import BeautifulSoup
import logging
import warnings
import cPickle as pickle
import string
from sys import argv
import boto3

warnings.filterwarnings('ignore')
logging.basicConfig(filename='scrape.log',level=logging.ERROR)

def openStates(filepath):
    ''' opens csv of urls for state brewery listings
        input: csv of state brewery urls
        output: list of state brewery urls'''
    with open(filepath) as states:
        urls = states.read().split(',')
    return urls


def _getBreweries(url):
    ''' gets list of active brewery review page urls 
        INPUT: URL for state brewery list
        OUTPUT: list of brewery URLS'''
    brewery_list = []
    try: html = urllib2.urlopen(url)
    except:
        logging.error(url)
        print url
    else:
        soup = BeautifulSoup(html)
        data = soup.findAll('div', attrs={'class':'active'})
        for div in data:
            for a in div.findAll('a'):
                if a['href'][:9] == '/brewers/':
                    brewery_list.append('http://www.ratebeer.com{}'.format(a['href']))
    return brewery_list

def collectBreweries(url_list):
    '''creates dict with states and lists of breweries.
        input: list of urls pointing to state brewery pages
        output: dict with states as keys and lists of breweries in that state as values'''
    dict_urls = {}
    for url in url_list:
        state = url.split('/')[-4]
        dict_urls['{}'.format(state)] = _getBreweries(url)
    return dict_urls

def _tenPlus(BeautifulSoupObject):
    '''returns True if a beer has 10 or more reviews, else returns False
        input: beautifulsoup object
        output: boolean'''
    try:
        num_reviews = int(BeautifulSoupObject.findAll('td', attrs={'class':'text-left'})[-1].text)
    except:
        return False
    else:
        if num_reviews >= 10:
            return True
        else:
            return False

def _getBeers(url):
    '''creates a list of urls to beer review pages with 10 or more reviews for a given brewery
        INPUT: url of brewery page
        Output: list of beer urls for brewery'''
    beer_urls = []
    try:
        html = urllib2.urlopen(url)
        soup = BeautifulSoup(html)
        table = soup.find('tbody')
        beers = table.findChildren('tr')
        for tr_tag in beers:
            if _tenPlus(tr_tag):
                url = tr_tag.find('strong').findChild('a')['href']
                beer_urls.append(u'http://www.ratebeer.com' + url )
            else:
                pass
    except:
        logging.error(url)
        print 'error...',url    
    else:
        pass

    return beer_urls

def collectBeers(state_dict):
    '''returns a dict of dicts of breweries and their beers
        input: dict created by collectbreweries function
        output: dict of states containing dicts of 
        breweries and urls for their beers with 10+ reviews'''
    beer_dict = {}
    for state in state_dict.keys():
        beer_dict[state] = {}
        for brewery_url in state_dict[state]:
            beers = _getBeers(brewery_url)
            if len(beers) > 0:
                beer_dict[state][brewery_url.split('/')[-3]] = beers
            else:
                continue
    return beer_dict

def pickleDict(a_dict, filename):
    ''' pickles the dict object
        input: dict to pickle
        output: pickle saved to directory'''
    with open(filename, 'w') as f:
        pickle.dump(a_dict, f, -1)

def getText(soup):
    '''
    INPUT: beautifulsoup object created from RB review page
    OUTPUT: list of review text in lowercase w/ puncuation and newlines removed'''
    textlist = []
    for i in soup.findAll('div', style="padding: 20px 10px 20px 0px; border-bottom: 1px solid #e0e0e0; line-height: 1.5;"):
        t = i.text.lower().replace('\n', ' ')
        t = t.replace('\r', '')
        textlist.append(''.join(s for s in t if s not in string.punctuation))
    return textlist

def getNames(soup):
    '''retrieves the brewery name and beer name from BS obj created from RB review page
    input: beautifulsoup object created from RB review page
    output: [<beer>, <brewery>]'''

    names = []
    for name in soup.findAll('span', itemprop='name'):
        names.append(name.text)
    if len(names) > 1:
        return names[0], names[1]
    else:
        return u'none', u'none'

def getUsers(soup):
    '''retrieves the usernames and beer name from BS obj created from RB review page
    input: beautifulsoup object created from RB review page
    output: list of tuples w/ (username, ID) for each review'''
    users = []
    for a in soup.findAll('a', href=True):
        if a['href'][:6] == '/user/':
            user = a.text.encode('utf8').decode('ascii', 'ignore').split('(')[0]
            userid = a['href'][6:-1]
            users.append((user, userid))
    return users

def getAbv(soup):
    '''retrieves the ABV of a beer
    input: beautifulsoup object created from RB review page
    output: float or 'none' if no ABV is available'''
    beer_data = []
    for big in soup.findAll('big', style='color: #777;'):
        beer_data.append(big.text)
    if beer_data[-1][-1] == '%':
        return float(beer_data[-1][:-1])
    else:
        return u'none'

def getStyle(soup):
    '''retrieves the style of a beer
    input: beautifulsoup object created from RB review page
    output: float or 'none' if no style is available'''
    style = []
    for a in soup.findAll('a', href=True):
        if a['href'][:12] == '/beerstyles/':
            style.append(a.text)
    if len(style) > 0:
        return style[0]
    else:
        return u'none'

def getRatings(soup):
    '''retrieves the ratings from a RB review page
    input: beautifulsoup object created from RB review page
    output: list of lists containing the ratings from the RB review page'''
    ratings = []
    for strong in soup.findAll('strong'):
            s = strong.text.split()
            if s[0] == 'AROMA':
                rate_num = [x.split('/') for x in s[1::2]]
                num_list = []
                for i in rate_num:
                    num_list.append(int(i[0]))
                for i in xrange(0, len(num_list)-1, 5):
                    ratings.append(num_list[i:i+5]) 
    return ratings

def getPagination(html):
    '''returns the number of pages that the reviews are paginated over'''
    page_nums = []
    soup = BeautifulSoup(html)
    for i in soup.findAll(class_ = 'ballno'):
        page_nums.append(i.text)
    if len(page_nums) > 0:
        return int(page_nums[-1])
    else:
        return 1

def collectReviewSoup(url):
    ''' input: url of RB beer review page
        output: list of soup objects containing all review pages for that beer'''
    num_pages = getPagination(urllib2.urlopen(url))
    soup_docs = []
    for page in range(1, num_pages + 1):
        url_format = url + '1/{}/'.format(str(page))
        html = urllib2.urlopen(url_format)
        soup_docs.append(BeautifulSoup(html))
    return soup_docs


def collectReviews(beer_url):
    ''' creates a list of dicts for all reviews of given beer
        input: list of html docs
        output: json of review data'''
    out = []
    try:
        soup_list = collectReviewSoup(beer_url)
    except:
        logging.error('{}'.format(beer_url))
        print 'error collecting reviews', beer_url
        return out
    else:
        for i in soup_list:
            soup = i
            beer_name, brewery_name = getNames(soup)
            style = getStyle(soup)
            users = getUsers(soup)
            ratings = getRatings(soup)
            text = getText(soup)
            beer_id = int(beer_url.split('/')[-2])
            for i, rating in enumerate(ratings):
                out.append({
                    'beername' : beer_name,
                    'beerid' : beer_id,
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
    return out

def getStateReviews(state, beer_dict):
    '''input: state string, dictionary created with collect beers function
        output: list of dicts contining data for all beers in state string'''
    review_data = []
    for brewery, beers in beer_dict[state].iteritems():
        for url in beers:
            review_data.extend(collectReviews(url))
    return review_data

def s3dump(key, data):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('bucketofbeer')
    bucket.put_object(Key=key, Body=data)

if __name__ == "__main__":
    #fpath = argv[1]
    #stateurls = openStates(fpath)
    #print 'state urls collected'
    #print 'collecting brewery urls...'
    #brewery_urls = collectBreweries(stateurls)
    #print 'brewery urls collected'
    #print 'saving brewery urls...'
    #pickleDict(brewery_urls, 'brewery_urls.pkl')
    #print 'brewery urls saved'
    pkl_file = argv[1]
    with open(pkl_file, 'r') as f:
        beer_urls = pickle.load(f)
    #print 'collecting beer urls...'
    #beer_urls = collectBeers(brewery_urls)
    #print '...completed'
    #print 'saving beer urls'
    #pickleDict(beer_urls, 'brewery_urls.pkl')
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('bucketofbeer')
    completed = [x.key for x in bucket.objects.all()]
    for state in beer_urls.keys():
        if '{0}.pkl'.format(state) not in completed:
            print 'collecting reviews for', state
            reviews = getStateReviews(state, beer_urls)
            print 'saving reviews for', state
            rev_pickle = pickle.dumps(reviews)
            s3dump('{}.pkl'.format(state), rev_pickle)
            print 'reviews for {} saved'.format(state)





