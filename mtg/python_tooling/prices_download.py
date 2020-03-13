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

import serialize

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
	multiverse_ids = []

	for line in sys.stdin.readlines():
		multiverse_ids.append(int(line))

	a = ScryfallAPI()
	# a = MockAPI()

	dump = []
	signal.signal(signal.SIGTERM, signal_handler_raise_exception)
	try:
		for multiverse_id in multiverse_ids:
			time.sleep(1.0 / 8.0)
			r = a.prices_request(multiverse_id)
			now = datetime.datetime.utcnow()
			rr = serialize.PriceRecord(multiverse_id, *r[1:], now.year, now.month, now.day)
			print(r[0], multiverse_id, rr.USD, rr.EUR)
			dump.append(rr)

	except BaseException as e:
		print(e.__class__.__name__, str(e))
	finally:
		serialize.to_file("e_data", dump) # cleanup

	# print(list(from_file("e_data")))

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
