import statistics

def extract_price(date_price):
	l = sorted(list(date_price.values()))
	if len(l) < 3:
		return l[0]

	margin = len(l) // 3
	sublist = l[margin:-margin]
	return statistics.fmean(sublist)

def price_pair(provider):
	retail = provider.get("retail")
	if retail is None:
		return (None, None)

	normal_price = None
	foil_price = None

	normal = retail.get("normal", None)
	if normal:
		normal_price = extract_price(normal)
	foil = retail.get("foil", None)
	if foil:
		foil_price = extract_price(foil)
	return (normal_price, foil_price)

def safe_mul(a, b):
	if a is None or b is None:
		return None
	return a * b

def safe_div(a, b):
	if a is None or b is None:
		return None
	return a / b

def convert_currency(source, conversion):
	return (safe_mul(source[0], conversion), safe_mul(source[1], conversion))

class mtg_json:
	def __init__(self):
		self.name_to_multiverse_id = dict()
		# self.name_to_mcm_id = dict()
		self.multiverse_id_to_name = dict()
		# self.multiverse_id_to_mcm_id = dict()
		# self.mcm_id_to_name = dict()
		self.mcm_id_to_multiverse_id = dict()

		self.buy_dict = dict()

	def extract(self, data):
		for uid, values in data["data"].items():
			name = values.get("name")
			scid = values.get("identifiers", {}).get("scryfallId")
			sclink = "https://scryfall.com/card/" + scid
			plink = values.get("purchaseUrls", {}).get("tcgplayer")
			self.buy_dict[uid] = {"name": name, "uid": uid, "link": plink, "scryfall": sclink}

	def prices(self, data):
		sorted = dict()

		for uid, values in data["data"].items():
			paper = values.get("paper")
			if paper:
				tcg_prices = (None, None)
				mcm_prices = (None, None)

				tcg = paper.get("tcgplayer")
				if tcg:
					tcg_prices = price_pair(tcg)
					if tcg["currency"] != "USD":
						print("ERROR")

				mcm = paper.get("cardmarket")
				if mcm:
					mcm_prices = price_pair(mcm)
					if mcm["currency"] != "EUR":
						print("ERROR")

				converted_tcg = convert_currency(tcg_prices, 4.0)
				converted_mcm = convert_currency(mcm_prices, 4.5)

				ratio_normal = safe_div(converted_tcg[0], converted_mcm[0])
				ratio_foil = safe_div(converted_tcg[1], converted_mcm[1])
				info = self.buy_dict.get(uid)

				if ratio_normal and converted_mcm[0] > 3.0:
					print(ratio_normal, "NORMAL", converted_tcg[0], converted_mcm[0], info)
				if ratio_foil and converted_mcm[1] > 3.0:
					print(ratio_foil, "FOIL", converted_tcg[1], converted_mcm[1], info)
