import argparse
import datetime
import enum
import html.parser
import http
import http.client
import json
import re
import signal
import sys
import threading
import time

import concurrent_do
import mtg_json

def strip_whitespace(s):
	split = re.split(r"\s+", s)
	none_removed = list(filter(None, split))
	return " ".join(none_removed)

class matching_parser(html.parser.HTMLParser):
	def __init__(self, pattern):
		super().__init__()
		self.found = []
		self.incoming = False
		self.pattern = pattern

	def handle_data(self, data_not_stripped):
		data = strip_whitespace(data_not_stripped)
		if not data:
			return
		if self.incoming:
			self.found.append(data)
			self.incoming = False
		if data == self.pattern:
			self.incoming = True


def download(connection, multiverseid):
	resource = "/Pages/Card/Details.aspx?multiverseid=" + str(multiverseid)
	connection.request("GET", resource, headers = {"Connection":" keep-alive"})
	response = connection.getresponse()
	print(response.getheaders())
	content = response.read()
	if response.status != http.HTTPStatus.OK.value:
		if response.status != http.HTTPStatus.FOUND.value:
			print("Id", multiverseid, "status", response.status)
		return response.status, None
	return response.status, content


def get_names(content):
	""" There are cards with multiple names: split, Fuse, Kamigawa's flip, transform, Aftermath etc.
	"""
	parser = matching_parser("Card Name:")
	parser.feed(content.decode("utf-8"))
	return parser.found


def get_data_for_id(connection, multiverseid):
	status, content = download(connection, multiverseid)
	if content is None:
		return None
	names = get_names(content)
	return names

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

class DOERS:
	def __init__(self, first, last, connections):
		self.connections = connections
		self.first = first
		self.last = last
		self.data = [None] * (self.last)

	def json(self):
		tmp = dict()
		for n, v in enumerate(self.data):
			if not v is None:
				tmp[n] = v
		print(json.dumps(tmp))

	def workers(self):
		for _ in range(self.connections):
			yield self.Inner()

	def jobs(self):
		yield from range(self.first, self.last)

	def parallel_work(self, worker, job):
		# self is shared!
		return worker.parallel_work(job)

	def merge(self, worker, job, result):
		eprint(job, result)
		self.data[job] = result

	class Inner:
		def __init__(self):
			self.connection = None

		def parallel_work(self, i):
			if self.connection is None:
				self.connection = http.client.HTTPSConnection("gatherer.wizards.com")

			return get_data_for_id(self.connection, i)

def merge_alternate(a, b):
	k = min(len(a), len(b))
	result = [None] * (k * 2)
	result[::2] = a[:k]
	result[1::2] = b[:k]
	result.extend(a[k:])
	result.extend(b[k:])
	return result

def remove_duplicates_keeping_order(l):
	ret = []
	s = set()
	for x in l:
		if not x in s:
			s.add(x)
			ret.append(x)
	return ret

import price_record

class ScryfallAPI:
	def __init__(self):
		self.connection = http.client.HTTPSConnection("api.scryfall.com")

	def prices_request(self, multiverse_id):
		# Watch for HTTP 429 too many requests (scryfall API guide)
		# if response.status != http.HTTPStatus.OK.value:
		resource = "/cards/multiverse/" + str(multiverse_id)
		self.connection.request("GET", resource, headers = {"Connection":" keep-alive"})
		response = self.connection.getresponse()
		content = response.read()
		# print(response.getheaders())
		# print(response.status)
		# print(content)
		l = json.loads(content)

		def check(p):
			if p is None:
				return None
			try:
				return float(p)
			except ValueError:
				return None
		prices = l["prices"]
		return (l["name"], check(prices["usd"]), check(prices["usd_foil"]), check(prices["eur"]), None, check(prices["tix"]), None)

class MockAPI:
	def prices_request(self, multiverse_id):
		return ("Mock Card", 1.0, 2.0, 3.0, None, 5.0, None)

def signal_handler_raise_exception(signum, frame):
	raise OSError("Arbitrary string. Signal " + str(signum))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Prepare data from mtgjson.com files. Take multiple json files and output one.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('prices', help='price files', nargs='*')
	parser.add_argument('--mtg-json', help='mtg json data file')
	parser.add_argument('--output', help='output price file', required=True)
	parser.add_argument('--merge', action='store_true')
	parser.add_argument('--verbose', action='store_true')

	args = parser.parse_args()
	prices_by_multiverse_id = price_record.merge(args.prices)

	print("Found ", len(prices_by_multiverse_id), "records.")
	query_list = []

	if args.mtg_json is not None:
		data = mtg_json.mtg_json()
		with open(args.mtg_json, 'r') as f:
			data.extract(json.load(f))

		print("Found ", len(data.by_multiverse_id), "unique multiverse_ids.")
		for (k, v) in data.by_multiverse_id.items():
			if not k in prices_by_multiverse_id:
				query_list.append(k)
		query_list.sort(reverse=True)

	if args.verbose:
		print("Calculating delays...")
		now = datetime.datetime.utcnow()
		one_divided_by_count = 1.0 / len(prices_by_multiverse_id)
		total = datetime.timedelta()
		for record in prices_by_multiverse_id.values():
			then = price_record.date_from_record(record)
			elapsed = now - then
			total += elapsed * one_divided_by_count
		print("Average price check delay", total)

	sorted_by_date  = [r.multiverse_id for r in sorted(prices_by_multiverse_id.values(), key = lambda x: price_record.date_from_record(x))]
	sorted_by_multiverse_id = sorted(prices_by_multiverse_id.keys(), reverse=True)
	query_list += remove_duplicates_keeping_order(merge_alternate(sorted_by_date, sorted_by_multiverse_id))

	a = ScryfallAPI()
	# a = MockAPI()

	DELAY_BETWEEN_REQUESTS_IN_SECONDS = 0.1
	dump = dict()
	if args.merge:
		dump = prices_by_multiverse_id
	signal.signal(signal.SIGTERM, signal_handler_raise_exception)
	try:
		total = len(query_list)
		for i, multiverse_id in enumerate(query_list, start=1):
			time.sleep(DELAY_BETWEEN_REQUESTS_IN_SECONDS)
			response = a.prices_request(multiverse_id)
			record = price_record.make_price_record(multiverse_id, *response[1:])
			print(response[0], multiverse_id, record.USD, record.EUR, "{} of {}".format(i, total))
			dump[multiverse_id] = record
	#except BaseException as e:
	#	print(e.__class__.__name__, str(e))
	finally:
		price_record.to_file(args.output, dump.values()) # cleanup

# this is just old code just to test getting data from official WotC site
if __name__ == "__main__2":
	parser = argparse.ArgumentParser(description='Downloads data from the gatherer.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--connections', default=8, type=int)
	parser.add_argument('--threads', default=4, type=int)

	parser.add_argument('--first', default=1, type=int)
	parser.add_argument('--last', default=10, type=int)

	args = parser.parse_args()

	d = DOERS(args.first, args.last, args.connections)
	try:
		z = concurrent_do.concurrent_do(d, args.threads)
		z.start()
		z.close()
	finally:
		d.json()
