import argparse
import concurrent.futures
import enum
import html.parser
import http
import http.client
import json
import re
import sys
import threading
import time

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
	# print(response.getheaders())
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
		self.i = self.first
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

	def synchronous_generate(self, inner_instance):
		if self.i >= self.last:
			return None

		tmp = self.i
		self.i += 1
		return tmp

	def parallel_work(self, inner_instance, i):
		# self is shared!
		return inner_instance.parallel_work(i)

	def synchronous_merge(self, inner_instance, i, work):
		eprint(i, work)
		self.data[i] = work

	def synchronous_close(self, inner_instance):
		inner_instance.synchronous_close()

	class Inner:

		def __init__(self):
			self.connection = None

		def parallel_work(self, i):
			if self.connection is None:
				self.connection = http.client.HTTPConnection("gatherer.wizards.com")

			return get_data_for_id(self.connection, i)

		def synchronous_close(self):
			if self.connection is not None:
				self.connection.close()


class concurrent_do:
	def __init__(self, doers, number_of_threads):
		self.doers = doers
		self.clients_executor = concurrent.futures.ThreadPoolExecutor(max_workers = number_of_threads)

	def close(self):
		self.clients_executor.shutdown()

	def do(self):
		to_do = set()
		for x in self.doers.workers():
			self.master_continue(to_do, x)

		while to_do:
			done, not_done = concurrent.futures.wait(to_do, timeout=None, return_when=concurrent.futures.FIRST_COMPLETED)
			to_do = not_done
			for future in done:
				x, i, work = future.result()
				self.doers.synchronous_merge(x, i, work)
				self.master_continue(to_do, x)

	def master_continue(self, futures_set, x):
		i = self.doers.synchronous_generate(x)
		if i is None:
			self.doers.synchronous_close(x)
			return
		future = self.clients_executor.submit(self.worker_work, x, i)
		futures_set.add(future)

	def worker_work(self, x, i):
		return x, i, self.doers.parallel_work(x, i)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Downloads data from the gatherer.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--connections', default=8, type=int)
	parser.add_argument('--threads', default=4, type=int)

	parser.add_argument('--first', default=1, type=int)
	parser.add_argument('--last', default=10, type=int)

	args = parser.parse_args()

	d = DOERS(args.first, args.last, args.connections)
	try:
		z = concurrent_do(d, args.threads)
		z.do()
		z.close()
	finally:
		d.json()
