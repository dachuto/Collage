import argparse

import json

import http
import http.client

import base64
import hashlib
import hmac
import sys
import time
from urllib.parse import urlencode
from urllib.parse import quote

import xml.etree.ElementTree as XML

class CONST:
	idProduct = "idProduct"
	comments = "comments"
	price = "price"
	count = "count"
	condition = "condition"
	isFoil = "isFoil"
	isPlayset = "isPlayset"

### parsing XML from cardmarket

def unique_tag(node, tag):
	# print(node.tag, node.attrib, node.text)
	l = node.findall(tag)
	if len(l) == 0:
		return None
	return l[0]

def articles_from_xml(s):
	root = XML.fromstring(s)
	for e in root.findall("article"):
		print(XML.tostring(e))
		mcm_id = unique_tag(e, CONST.idProduct).text
		price_EUR = unique_tag(e, CONST.price).text
		is_foil = unique_tag(e, CONST.isFoil).text # "false" // "true"
		#"condition"
		assert mcm_id is not None
		assert price_EUR is not None
		yield (mcm_id, p)

def articles_from_json(s):
	root = json.loads(s)
	for i in root["article"]:
		yield i

class CardmarketAPI:
	def __init__(self, app_token, app_secret, access_token, access_token_secret):
		self.app_token = app_token
		self.app_secret = app_secret
		self.access_token = access_token
		self.access_token_secret = access_token_secret

	def request(self, location, additional_params):
		nonce_str = "53ax1f44909d6" # random
		base_uri = "https://api.cardmarket.com"

		paramless_uri = base_uri + location
		full_uri = paramless_uri
		if additional_params:
			full_uri += "?" + urlencode(additional_params)

		base_str = "GET&" + quote(paramless_uri, safe="") + "&"
		# print(base_str)
		time_str = str(int(time.time()))
		# print(time_str)

		auth_params = {
			"oauth_consumer_key":self.app_token,
			"oauth_nonce":nonce_str,
			"oauth_timestamp":time_str,
			"oauth_token":self.access_token,
			"oauth_signature_method":"HMAC-SHA1",
			"oauth_version":"1.0",
		}
		auth_params.update(additional_params)
		auth_params = sorted(auth_params.items())
		auth_params_str = quote(urlencode(auth_params))
		# print(auth_params_str)
		signing_key = quote(self.app_secret) + "&" + quote(self.access_token_secret)
		# print(signing_key)
		# print(base_str + auth_params_str)

		key_bytes = bytearray(signing_key, encoding='ascii')
		msg_bytes = bytearray(base_str + auth_params_str, encoding='ascii')

		hashed = hmac.new(key_bytes, msg_bytes, hashlib.sha1)
		signature_str = base64.b64encode(hashed.digest()).decode("utf-8")
		# print(signature_str)

		def param_to_str(k, v):
			return " " + k + '="' + v + '"'
		auth_str = "OAuth"
		auth_str += param_to_str("realm", paramless_uri) + ","
		for (k, v) in auth_params:
			auth_str += param_to_str(k, v) + ","
		auth_str += param_to_str("oauth_signature", signature_str)
		# print(auth_str)

		connection = http.client.HTTPSConnection("api.cardmarket.com")
		# connection.set_debuglevel(1)
		http_params = {"Authorization": auth_str}
		connection.putrequest("GET", full_uri, skip_host=True, skip_accept_encoding=True)
		connection.putheader("Authorization", auth_str)
		connection.endheaders()
		response = connection.getresponse()
		content = response.read()
		# print(response.getheaders())
		return (response.status, content.decode('utf-8'))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Gets market data from cardmarket.com api', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	group = parser.add_argument_group(title='secret stuff from your cardmarket account')
	group.add_argument('--app-token', required=True)
	group.add_argument('--app-secret', required=True)
	group.add_argument('--access-token', required=True)
	group.add_argument('--access-token-secret', required=True)
	commands = parser.add_mutually_exclusive_group(required=True)
	commands.add_argument('--user')
	commands.add_argument('--products-download', metavar='FILENAME', help='downloads a file with all products on the market')

	args = parser.parse_args()

	api = CardmarketAPI(args.app_token, args.app_secret, args.access_token, args.access_token_secret)

	if args.user:
		location = "/ws/v2.0/output.json/users/" + args.user + "/articles"

		i = 0
		batch = 1000
		articles = []
		while True:
			additional_params = {"start":str(i), "maxResults":str(batch)}

			print("request articles " + str(i) + " to " + str(i + batch), file=sys.stderr)
			status, content = api.request(location, additional_params)
			if status != http.HTTPStatus.OK.value and status != http.HTTPStatus.PARTIAL_CONTENT.value:
				print("HTTP response " + str(status), file=sys.stderr)
				break
			# articles_from_xml(content)
			how_many_in_batch = 0
			for a in articles_from_json(content):
				articles.append(a)
				how_many_in_batch += 1

			i += batch
			if how_many_in_batch < batch:
				break

		with open("user_cardmarket_" + args.user + ".json", "w") as file:
			json.dump(articles, file)

	elif args.products_download:
		location = "/ws/v2.0/productlist"
		additional_params = {}
		status, content = api.request(location, additional_params)
		# tree = XML.parse('products.xml')
		# root = tree.getroot()
		root = XML.fromstring(content)
		decoded = base64.b64decode(unique_tag(root, "productsfile").text)
		with open(args.products_download, "wb") as file:
			file.write(decoded)
