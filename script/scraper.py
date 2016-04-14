import warnings
import requests
from bs4 import BeautifulSoup
import boto
import json
warnings.filterwarnings('ignore')
from sys import argv
import json
import string

# get pagiation
def get_page_num(url):
    '''
    input: ratebeer.com url
    output: the number of pages that hold data '''
    
    page_nums = []
    r = requests.get(url)
    soup = BeautifulSoup(r.content)
    for i in soup.findAll(class_ = 'ballno'):
        page_nums.append(i.text)
    if len(page_nums) > 0:
        return int(page_nums[-1])
    else:
        return 1


#list of request objects
def brewery_req(char_list):
    '''
    input: list of alphanumeric characters
    output: list of html requests for every brewery
    listing page associated with those characters'''
    
    request_list = []
    for letter in char_list:
        request_list.append(requests.get('http://www.ratebeer.com/browsebrewers-{}.htm'.format(letter)))
    return request_list


# dict of {brewery : url} associations
def get_brew_urls(req_list):
    '''
    input: list of html request objects from brewery listing pages
    output: dict of {brewery : url} associations '''
    
    brew_urls = {}
    for req in req_list:
        soup = BeautifulSoup(req.content)
        for a in soup.findAll('a'):    
            if a['href'][:9] == '/brewers/':
                brew_urls[u'{0}'.format(a.text)] = u'http://www.ratebeer.com{}'.format(a['href'])
    return brew_urls


# get html requests for each page of beer listings for a single brewery
def beer_reqs(brewery, brew_urls):
    '''
    input: name of brewery, dict of brewery:url pairs
    output: list of html requests for every page of
    beer listings associated with that brewery'''
    request_list = []
    base_url = brew_urls[brewery]
    for page in xrange(1,get_page_num(base_url)+1):
        request_list.append(requests.get('{0}0/{1}/'.format(base_url, page)))
    return request_list


# get dict of {beer:url} pairs for each brewery
def get_beer_url_dict(req_list):
    '''
    input: list of html requests from brewery page(s)
    output: dict of {beer name:url pairs}'''
    beer_dict = {}
    for req in req_list:
        soup = BeautifulSoup(req.content)
        for a in soup.findAll('a'):
            if (a['href'][:6] == '/beer/') and \
            (a['href'][5:11] != '/rate/') and \
            (a['href'][5:13] != '/top-50/'):
                beer_dict[u'{0}'.format(a.text)] = u'http://www.ratebeer.com{}'.format(a['href'])
    return beer_dict


def review_reqs(beer, beer_dict):
    '''
    input: beer, dict of 
    output: html request for the review page(s)'''
    request_list = []
    url = beer_dict[beer]
    for page in xrange(1,get_page_num(url)+1):
        request_list.append(requests.get('{0}1/{1}/'.format(url, page)))
    return request_list


def form_text(soup):
    '''
    INPUT: beautifulsoup object created from RB review page
    OUTPUT: list of review text in lowercase w/ puncuation removed'''
    textlist = []
    for i in soup.findAll('div', style="padding: 20px 10px 20px 0px; border-bottom: 1px solid #e0e0e0; line-height: 1.5;"):
        t = i.text.lower()
        textlist.append(''.join(s for s in t if s not in string.punctuation))
    return textlist

def get_review(req_list):
    '''
    input: list of html requests from beer review page(s)
    output: list of lists containing review data'''

    complete = []
    for page in req_list:
        page_reviews = []
        users = []
        soup = BeautifulSoup(page.content)
        textlist = form_text(soup)
        for strong in soup.findAll('strong'):
            s = strong.text.split()
            if s[0] == 'AROMA':
                page_reviews.append(s[1::2])
        for a in soup.findAll('a', href=True):
            if a['href'][:6] == '/user/':
                users.append(a.text.split()[0])
        for i, user in enumerate(users):
            page_reviews[i].append(user)
            page_reviews[i].append(textlist[i])
        complete.extend(page_reviews)
    return complete



if __name__ == "__main__":
	conn = boto.connect_s3()
	bob = conn.get_bucket('bucketofbeer')
	url_list = argv[1:]
	alpha_range = '{0}_{1}'.format(url_list[0],url_list[-1])

	r = brewery_req(url_list)
	url_dict = get_brew_urls(r)
	num_url = len(url_dict)
	print '{} brewery urls recorded'.format(num_url)
	#file = bob.new_key(
	#	'/data/brewery_url_{0}.txt'.format(alpha_range))
	#file.set_contents_from_string('{}'.format(url_dict))
	
	for i, brewery in enumerate(url_dict.keys()):

		print 'requesting {0} of {1} beer lists'.format(str(i), num_url)
		r = beer_reqs(brewery, url_dict)
		print '...complete'
		
		beer_dict = get_beer_url_dict(r)
		b_format = url_dict[brewery].split('/')[-3]
		brewery_id = url_dict[brewery].split('/')[-2]
		num_beers = len(beer_dict)
	#	file = bob.new_key(
	#		'/data/{0}/{1}.txt'.format(alpha_range, b_format))
		
	#	print 'writing {} to s3'.format(b_format)
	#	file.set_contents_from_string('{}'.format(beer_dict))
	#	print 'writing complete: '
		

		for i, beer in enumerate(beer_dict.keys()):
			beer_name = beer_dict[beer].split('/')[-3]
			beer_id = beer_dict[beer].split('/')[-2]
			file = bob.new_key(
					'/data/{0}/{1}/{2}.csv'.format(alpha_range, b_format, beer_id))
			print '{0} of {1}, requesting reviews for {2}...'.format(
				i, num_beers, beer_name)
			r = review_reqs(beer, beer_dict)
			print'...complete'
			out = []
			reviews = get_review(r)
			if len(reviews) > 0:
				for review in reviews:
					review.extend([beer, beer_id, brewery, brewery_id])
					out.append(','.join(review))
				out = '\n'.join(out)
				print 'writing reviews to csv...'
				file.set_contents_from_string('{}'.format(out.encode('utf8')))
				print '...complete'
			else:
				print 'no reviews'



















