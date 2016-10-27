import requests
import threading
from bs4 import BeautifulSoup
import Queue
from sys import argv

def formUrl(user_id, page):
  return 'https://www.ratebeer.com/ajax/user/{0}/beer-ratings/{1}/5/'.format(user_id, page) 


def getPagnination(soup):
  try:
    pages = int(soup.ul.findChildren()[-1]['href'].split('/')[-3])
  except:
    pages = 1
  return pages

def reviewPages(user_id):
  intitial = formUrl(user_id, 1)
  soup = BeautifulSoup(requests.get(intitial).text)
  pages = getPagnination(soup)
  urls = []
  for i in xrange(1, pages + 1):
      urls.append(formUrl(user_id, i))
  return(urls)


def getReview(soup):
  div_curvy = soup.findAll('div', class_='curvy')
  for i in div_curvy[-1].text.split('/'):
    if u'OVERALL' in i:
        return int(i[-2:].strip())
  

def fetchreqs(url, out, get_id=False):
    req =  requests.get(url)
    if get_id == True:
      beer_id = getId(url)
      out.append((req, beer_id))
    else:
      out.append(req)

def threadedReqs(url_list, get_id=False):
  out = []
  if get_id == False:
    threads = [threading.Thread(target=fetchreqs, args=(url, out)) for url in url_list]
  else:
    threads = [threading.Thread(target=fetchreqs, args=(url, out, True)) for url in url_list]
  for thread in threads:
      thread.start()
  for thread in threads:
      thread.join()
  return out

def getSoup(reqs, get_id=False):
  if get_id == False:
    return [BeautifulSoup(req.text) for req in reqs]
  else:
    out = []
    for req, beer_id in reqs:
      out.append((BeautifulSoup(req.text), beer_id))
    return out


def reviewlinks(soup):
  links = []
  for a in soup.tbody.findAll('a'):
    if a['href'][:6] == u'/beer/':
        links.append(u'http://www.ratebeer.com' + a['href'])
  return links

def gatherReviewUrls(soup_list):
  url_list = []
  for soup in soup_list:
    url_list.extend(reviewlinks(soup))
  return url_list

def gatherReviews(soup_beerid_list):
  reviews = []
  for soup, beer_id in soup_beerid_list:
    review = getReview(soup)
    reviews.append((review, beer_id))
  return reviews



def getId(url):
  return int(url.split('/')[-3])


def scrapeProfile(user_id):
  # request all pages containing list of reviews beers
  pages = reviewPages(user_id)
  reqs = threadedReqs(pages)
  # create beautiful soup objects and parse for links to user reviews
  soups = getSoup(reqs)
  url_list = gatherReviewUrls(soups)
  # request all pages containing reviews and assemble list of review - beer id pairs
  url_reqs = threadedReqs(url_list, get_id=True)
  rev_soups = getSoup(url_reqs, get_id=True)
  return gatherReviews(rev_soups)

if __name__ == '__main__':
  scrapProfile(argv[1])




