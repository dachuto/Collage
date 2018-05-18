import concurrent.futures
import enum
import html.parser
import http
import http.client
import json
import re
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
	max_bytes = 128 * 1024 * 1024
	content = response.read(max_bytes)
	if response.status != http.HTTPStatus.OK.value:
		return response.status, None
	return response.status, content


def get_names(content):
	""" There are cards with multiple names: split, Fuse, Kamigawa's flip, transform, Aftermath etc.
	"""
	parser = matching_parser("Card Name:")
	parser.feed(content.decode("utf-8"))
	return parser.found


def get_data_for_id(connection, multiverseid):
	try:
		print("DOING", multiverseid)
		status, content = download(connection, multiverseid)
		if content is None:
			return status
		names = get_names(content)
		return names
	except Exception as e:
		print("BZZ EX")
		return e
	finally:
		print("DONE", multiverseid)


class DOERS:

	def __init__(self):
		self.biggest_id = 888888 + 2
		self.data = [None] * (self.biggest_id + 1)
		self.i = 888888

	def synchronous_new(self):
		return self.Inner()

	def synchronous_generate(self, inner_instance):
		if self.i >= self.biggest_id:
			return None

		self.i += 1
		return self.i

	def parallel_work(self, inner_instance, i):
		# self is shared!
		return inner_instance.parallel_work(i)

	def synchronous_merge(self, inner_instance, i, work):
		self.data[i] = work
		print(i, "=>", work)

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
			print("worker closing")
			if self.connection is not None:
				self.connection.close()


class concurrent_do:

	def __init__(self, doers, number_of_doers):
		self.number_of_doers = number_of_doers
		self.active = self.number_of_doers
		self.is_done = threading.Event()
		self.doers = doers
		self.clients_executor = concurrent.futures.ThreadPoolExecutor(max_workers = self.number_of_doers)
		self.master_executor = concurrent.futures.ThreadPoolExecutor(max_workers = 1)
		future = self.master_executor.submit(self.master_start)

	def close(self):
		self.is_done.wait()
		self.clients_executor.shutdown()
		self.master_executor.shutdown()

	def master_start(self):
		for i in range(self.number_of_doers):
			x = self.doers.synchronous_new()
			self.master_continue(x)

	def master_continue(self, x):
		i = self.doers.synchronous_generate(x)
		print("generated", i)
		if i is None:
			print("active>", self.active)
			self.active -= 1
			self.doers.synchronous_close(x)
			print("active<", self.active)
			if self.active == 0:
				self.is_done.set()
			return
		self.clients_executor.submit(self.worker_work, x, i)

	def master_merge(self, x, i, work):
		self.doers.synchronous_merge(x, i, work)
		self.master_continue(x)

	def worker_work(self, x, i):
		work = self.doers.parallel_work(x, i)
		self.master_executor.submit(self.master_merge, x, i, work)


if __name__ == "__main__":
	d = DOERS()
	z = concurrent_do(d, 3)
	z.close()
#	try:
#		for i in range(426912, 426912 + 30):
#			data[i] = get_data_for_id(connection, i)
#	finally:
#		for i, name in enumerate(data):
#			if name != None:
#				print(i, name)
