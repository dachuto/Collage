from bs4 import BeautifulSoup
import logging
import urllib.request
import requests

import json
import re
import time

import difflib

class time_throttle:
	def __init__(self):
		self.last = None

	def throttle(self, wait_at_least_seconds):
		current_time = time.monotonic()
		if self.last is None:
			self.last = current_time
			return self.last

		time_elapsed = current_time - self.last
		seconds_to_wait = wait_at_least_seconds - time_elapsed
		if seconds_to_wait > 0.0:
			time.sleep(seconds_to_wait)
		self.last = time.monotonic()
		return self.last

def fetch_website(session, url):
	logging.debug("Fetching {}".format(url))
	headers = {
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'identity',
		'Sec-Fetch-Dest': 'document',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'none',
		'Sec-Fetch-User': '?1',
		'DNT': '1',
		'Sec-GPC': '1',
		'Connection': 'keep-alive'
	}

	attempts = 0
	delays = [181, 301, 602]
	while True:
		try:
			# response = session.get('http://example.com/cookies')
			response = session.get(url, headers=headers)
				# headers = response.info()
			return response.text
		except requests.exceptions.HTTPError as e:
			if response.status_code == 403:
				if attempts >= len(delays):
					raise e
				delay = delays[attempts]
				attempts += 1
				logging.debug("Encountered 403 attempt {} delay {}".format(attempts, delay))
				time.sleep(delay)
			else:
				raise e

def fetch_local_json(x):
	url = 'http://localhost:8080/query?' + x + '='

	with urllib.request.urlopen(url) as response:
		return json.loads(response.read().decode())

def card_name_to_set_printing():
	return fetch_local_json('card_name_to_set_printing')

def set_printing_to_prices():
	return fetch_local_json('set_printing_to_prices')

def scrape_cards(html):
	ret = []
	soup = BeautifulSoup(html, 'html.parser')
	table = soup.find('div', class_='table-body')
	rows = table.find_all('div', class_='row')
	for row in rows:
		ref = None
		foil = False
		price = None
		elements = row.find_all('div', class_='col-seller')
		for e in elements:
			all_a = e.find_all('a')
			if len(all_a) > 0:
				href = all_a[0]['href']
				ref = href
				break

		attribs = row.find_all('div', class_='product-attributes')
		for attrib in attribs:
			if 'Foil' in str(attrib):
				foil = True
				break

		prices = row.find_all('div', class_='price-container')
		for p in prices:
			val = p.find('span').text
			if val.endswith(' €'):
				price = val[:-2]
				break
		if ref is not None and price is not None:
			ret.append((ref, price, foil))

	return ret

def generate_set_long_name_to_code_map(data):
	ret = dict()
	for set in data["data"]:
		ret[set["name"]] = set["code"]
	return ret

def get_collector_number(card_printings, set_code):
	for printing in card_printings:
		if printing["set"] == set_code:
			return printing["collector_number"]

def get_most_reasonable_price(prices, foil):
	USD_TO_EUR = 0.92
	if foil:
		if 'mkmfoil' in prices:
			return prices['mkmfoil']
		if 'tcgfoil' in prices:
			return prices['tcgfoil'] * USD_TO_EUR
	# foils can fall here, it is intended
	if 'mkmnormal' in prices:
		return prices['mkmnormal']
	if 'tcgnormal' in prices:
		return prices['tcgnormal'] * USD_TO_EUR

def worth_it(market_price, actual_money_spent):
	profit = market_price - actual_money_spent
	return profit / actual_money_spent

def dict_get_close(d, key):
	match = difflib.get_close_matches(key, d.keys(), n=5, cutoff=0.1)
	if match:
		print("Match: ", match)
		return d[match[0]]

def process(data, set_map):
	name_to_printing = card_name_to_set_printing()
	printing_to_prices = set_printing_to_prices()

	pattern = r'^.+/([^/]+)/([^/]+)$'
	for href, price_str, foil in data:
		print(">", href, price_str, foil)
		match = re.match(pattern, href)

		set_name_obfuscated = match.group(1).replace("-", " ")
		if set_name_obfuscated.endswith(" Extras"):
			set_name_obfuscated = set_name_obfuscated[:-7]
		card_name_obfuscated = match.group(2).replace("-", " ")
		price = float(price_str.replace(",", "."))

		set_code = dict_get_close(set_map, set_name_obfuscated)
		card_printings = dict_get_close(name_to_printing, card_name_obfuscated)
		print("Guessed set code:", set_code)

		if card_printings is None:
			continue

		collector_number = get_collector_number(card_printings, set_code)
		if collector_number is None:
			print("Could not find collector number " + str(card_printings) + " " + set_code)
			continue

		price_key = set_code + "/" + collector_number
		if price_key in printing_to_prices:
			prices = printing_to_prices[price_key]
		else:
			prices = dict_get_close(printing_to_prices, price_key)
		market_price = get_most_reasonable_price(prices, foil)
		print(market_price, price)
		if market_price is not None and price is not None:
			print("worth " + str(worth_it(market_price, price + 0.1)))

if __name__ == "__main__":
	tt = time_throttle()

	with open('./SetList.json') as f:
		data = json.load(f)
		set_code_map = generate_set_long_name_to_code_map(data)

		user = 'Aionelol'
		# with open('./DUPA_mkm.html', 'r') as file:
		# 	file_content = file.read()

		i = 1
		while True:
			tt.throttle(15)

			# Create a session
			session = requests.Session()

			file_content = fetch_website(session, "https://www.cardmarket.com/en/Magic/Users/" + user + "/Offers/Singles?site=" + str(i))
			cards = scrape_cards(file_content)
			if len(cards) < 1:
				break
			process(cards, set_code_map)
