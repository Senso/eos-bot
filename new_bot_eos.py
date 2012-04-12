import re
import os
import sys
import json
import time
import random
import urllib
import urllib2
import httplib
import cookielib

# http://www.crummy.com/software/BeautifulSoup/
from BeautifulSoup import BeautifulSoup

CONFIG = 'config.txt'

def load_config():
	# Load main config file
	try:
		return json.load(open(CONFIG))
	except ValueError, e:
		print "Error parsing configuration %s: " % CONFIG, e
		sys.exit(1)
	
class Web:
	def __init__(self, conf):
		self.conf = conf
		self.cookie = cookielib.MozillaCookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie))
		self.load_cookie()

	def load_cookie(self):
		#if os.access("cookie.txt", os.W_OK):
		try:
			self.cookie.load('cookie.txt')
			if self.authenticate():
				self.cookie.save(filename='cookies.txt')
			else:
				self.cookie.clear()
				raise

		except:
			if self.authenticate():
				self.cookie.save(filename='cookies.txt')
			else:
				print 'Login failed, exiting.'
				sys.exit(1)			
		
	def authenticate(self):
		ret = read_page(conf['urls']['login'] %(conf['username'], conf['password'], random.random()))
		if ret == 'OK':
			return True
		else:
			return False
		
	def read_page(self, url):
		time.sleep(0.5)
		r = self.opener.open(url)
		return r.read()




if __name__ == '__main__':
	config = load_config()
	web = Web()
	