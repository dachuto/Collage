import enum
import json
import re

import html.parser
import urllib.request
import time

def strip_whitespace(s):
	split = re.split(r"\s+", s)
	none_removed = list(filter(None, split))
	return " ".join(none_removed)


class matching_parser(html.parser.HTMLParser):
	def __init__(self, pattern):
		super().__init__()
		self.found = None
		self.incoming = False
		self.pattern = pattern

	def handle_data(self, data_not_stripped):
		data = strip_whitespace(data_not_stripped)
		if not data:
			return
		if self.incoming:
			self.found = data
			self.incoming = False
		if data == self.pattern:
			self.incoming = True

def download_name(url):
	http_request = urllib.request.urlopen(url)
	# print(http_request)
	# print(http_request.msg)
	data = http_request.read()
	parser = matching_parser("Card Name:")
	parser.feed(data.decode("utf-8"))
	# print(parser.found)
	return parser.found

def get_data_for_id(multiverseid):
	name = None
	status = "OK"
	time_begin = time.perf_counter()
	try:
		url = "http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=" + str(multiverseid)
		print(url)
		name = download_name(url)
		status = name
	except urllib.error.HTTPError as e:
		status = str(e)
	time_end = time.perf_counter()
	print(str(multiverseid).ljust(20), status.ljust(40), str(time_end - time_begin) + "s", )
	return name

if __name__ == "__main__":
	biggest_id = 1000
	data = [None] * biggest_id
	try:
		for i in range(990, biggest_id):
			data[i] = get_data_for_id(i)
	finally:
		for i, name in enumerate(data):
			if name != None:
				print(i, name)
