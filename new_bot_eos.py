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

stores_sell_pat = re.compile('stores-sell-set-price\.php\?fsid=([0-9]+)\&amp\;sc_pid=([0-9]+)')
import_cat_pat  = re.compile('/eos/market-import-cat\.php\?cat=([0-9]+)')
buy_from_pat	= re.compile('mB\.buyFromMarket\(([0-9]+),[0-9]\)\;')
prod_name_pat   = re.compile('title=\"(.+?) \- Product not found in warehouse\."')

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
		self.stores = {}
		
		self.cookie = cookielib.MozillaCookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie))
		self.load_cookie()

	def load_cookie(self):
		#if os.access("cookie.txt", os.W_OK):
		try:
			self.cookie.load('cookie.txt')
			if self.authenticate():
				self.cookie.save(filename='cookie.txt')
			else:
				self.cookie.clear()
				raise

		except:
			if self.authenticate():
				self.cookie.save(filename='cookie.txt')
			else:
				print 'Login failed, exiting.'
				sys.exit(1)			
		
	def authenticate(self):
		ret = self.read_page(self.conf['urls']['login'] %(self.conf['username'], self.conf['password'], random.random()))
		if ret == 'OK':
			
			# This is needed to validate login
			d = self.read_page('http://www.ratjoy.com/eos/')
			return True
		else:
			return False
		
	def read_page(self, url):
		time.sleep(1.0)
		r = self.opener.open(url)
		return r.read()
		
	def has_no_listings(self, content):
		if content.find('No listings found') > -1:
			return True
		return False
	
	def buy_product(self, content, prod_name):
		soup = BeautifulSoup(content)
		prod_name_pat = re.compile("title\=\"%s\"" % prod_name)
		market_pat = re.compile("market_display_[0-9]+")
		
		for tr_tag in soup.findAll(id=market_pat):
			raw_tr = tr_tag.__str__()
			
			# Check if the product is really found in that <TR>
			search_prod = re.search(prod_name_pat, raw_tr)
			if search_prod:
				time.sleep(1.0)
				print '\t\tFound', prod_name
				derp = re.search(buy_from_pat, raw_tr)
				
				if derp:
					market_prod_id = derp.group(1)
					res = self.read_page(self.conf['urls']['buy_page'] % (market_prod_id, self.conf['buy_qty']))
					print '\t\tPurchase Result:', res
					return True
				else:
					print '\t\tFailed to find mB.buyFromMarket pattern'
		return False
		
	def parse_outofstock(self, div):
		fsid = None
		sc_pid = None
		cat = None
		prod_name = None
		
		raw_div = div.__str__()
		stores_sell = re.search(stores_sell_pat, raw_div)
		if stores_sell:
			fsid = stores_sell.group(1)
			sc_pid = stores_sell.group(2)
		import_cat = re.search(import_cat_pat, raw_div)
		if import_cat:
			cat = import_cat.group(1)
		prod_name = re.search(prod_name_pat, raw_div)
		if prod_name:
			prod_name = prod_name.group(1).strip()

		if prod_name and cat and fsid and sc_pid:
			print '\t', prod_name, 'is Out of Stock.'

			# 100 is probably overkill
			page_num = 1
			while page_num < 100:

				print "\t\tSearching page %s of import category for %s" % (page_num, prod_name)
				imp_page = self.read_page(self.conf['urls']['import_cat'] % (cat, page_num))
				
				if self.has_no_listings(imp_page):
					print '\t\tNo more listings for', prod_name
					break
				
				if self.buy_product(imp_page, prod_name):
					break
				else:
					page_num += 1

		else:
			print 'Problem parsing Store page'
	
	def get_store_inventory(self, store_id):
		self.stores[store_id] = {}
		
		source = self.read_page(self.conf['urls']['store_inv'] % store_id)
		
		pos = source.find('<div class="prod_choices">')
		if pos == -1:
			print "Unable to parse store %s" % store_id
			return False

		soup = BeautifulSoup(source[pos:])
		
		# THIS whole thing is really ugly.
		for div in soup.findAll('div'):
			try:
				dc = div['class']
			except KeyError:
				# Found a <div> without a 'class'
				continue
			
			if div['class'] == 'prod_choices_item':
				sub = div.contents[0].contents
				for a in sub:
					try:
						an = a.name
					except AttributeError:
						# Most likely HTML we don't need
						continue
					
					if a.name == 'div':
						self.parse_outofstock(div)




if __name__ == '__main__':
	config = load_config()
	web = Web(config)
	
	for store in config['stores']:
		print 'Parsing store', store
		web.get_store_inventory(store)