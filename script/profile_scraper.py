import requests
import thredding
from bs4 import BeautifulSoup
import Queue

def formUrl(user_id, page):
    return 'www.ratebeer.com/ajax/user/{0}/beer-ratings/{1}/5/'.format(user_id, page) 


def getPagnination(soup):
    return int(soup.ul.findChildren()[-1]['href'].split('/')[-3])

def ReviewUrls(user_id):
    intitial = formUrl(user_id, 1)
    soup = BeautifulSoup(requests.get(intitial).text)
    pages = getPagnination(soup)
    urls = Queue.Queue(maxsize=0)
    for i in xrange(1, pages + 1):
        urls.put(formUrl(user_id, i))
    return(urls)

def getReviews(urls):



def getReview(soup):
    soup.find('div', class_='curvy')

import Queue
import threading
import requests
import time

hosts = ["http://yahoo.com", "http://google.com", "http://amazon.com",
"http://ibm.com", "http://apple.com"]

queue = Queue.Queue()

class ThreadUrl(threading.Thread):
  """Threaded Url Grab"""
  def __init__(self, queue):
    threading.Thread.__init__(self)
    self.queue = queue

  def run(self):
    while True:
      #grabs host from queue
      host = self.queue.get()

      #grabs urls of hosts and prints first 1024 bytes of page
      url = urllib2.urlopen(host)
      print url.read(1024)

      #signals to queue job is done
      self.queue.task_done()

start = time.time()

