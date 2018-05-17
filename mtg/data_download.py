import json
import re

from html.parser import HTMLParser
from urllib.request import (urlopen, urlparse, urlunparse, urlretrieve)


def strip_whitespace(s):
# 	return " ".join(s.split())
	split = re.split(r"\s+", s)
	none_removed = list(filter(None, split))
	return " ".join(none_removed)


class MyHTMLParser(HTMLParser):

	def __init__(self, pattern):
		super().__init__()
		self.found = None
		self.incoming = False
		self.pattern = pattern

	def handle_starttag(self, tag, attrs):
		print("Start tag:", tag)
		for attr in attrs:
			print("	 attr:", attr)

	def handle_endtag(self, tag):
		print("End tag  :", tag)

	def handle_data(self, data_not_stripped):
		data = strip_whitespace(data_not_stripped)
		if not data:
			return
		if self.incoming:
			self.found = data
			self.incoming = False
		if data == self.pattern:
			self.incoming = True
		print("Data[", data, "]")

	def handle_comment(self, data):
		print("Comment  :", data)

	def handle_entityref(self, name):
		c = chr(name2codepoint[name])
		print("Named ent:", c)

	def handle_charref(self, name):
		if name.startswith('x'):
			c = chr(int(name[1:], 16))
		else:
			c = chr(int(name))
		print("Num ent  :", c)

	def handle_decl(self, data):
		print("Decl	 :", data)


def main(url):
	http_request = urlopen(url)
	print(http_request)
	print(http_request.msg)
	data = http_request.read()
	parser = MyHTMLParser("Card Name:")
	parser.feed(data.decode("utf-8"))
	print(parser.found)
	print(json.dumps({"ID":parser.found}))
	return


if __name__ == "__main__":
	main("http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=4805")
