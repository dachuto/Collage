import argparse
import logging
import json
import types

import price_record
import mtg_json
import summary

#################################

import csv

def cardmarket_csv_to_id_and_name(f):
	r = csv.reader(f)
	next(r) # skip the first line
	for row in r:
		yield (int(row[0]), row[1], row[3] == "Magic Single")

###########################

def worth_it(market_price, actual_money_spent):
	profit = market_price - actual_money_spent
	return profit / actual_money_spent

def bar_string(i):
	assert i >= 0
	full_bars = i // 8
	remainder = i % 8
	s = "█" * full_bars
	if remainder == 7:
		s += "▉"
	elif remainder == 6:
		s += "▊"
	elif remainder == 5:
		s += "▋"
	elif remainder == 4:
		s += "▌"
	elif remainder == 3:
		s += "▍"
	elif remainder == 2:
		s += "▎"
	elif remainder == 1:
		s += "▏"
	return s

def cool_bar_string(length, max_value, value):
	i = int(length * 8 * value / max_value)
	if value > max_value:
		i = length * 8
	return bar_string(i).ljust(length, " ")

############################
def multiverse_id_with_best_price(price_by_multiverse_id, multiverse_ids, price_getter):
	def is_new_better_considering_nones(old_price, new_price):
		if new_price is None:
			return False
		if old_price is None:
			return True
		return old_price > new_price

	best_price = None
	best_record = None
	for multiverse_id in multiverse_ids:
		if multiverse_id is None:
			continue
		record = price_by_multiverse_id.get(multiverse_id, None)
		if record is None:
			continue
		price = price_getter(record)
		if is_new_better_considering_nones(best_price, price):
			best_price = price
			best_record = record
	return best_price, best_record

############################

CONVERSION_USD_TO_EUR = 0.85

def value_based_on_market(mcm_id, mcm_csv_name, is_foil, mtg_json_data, prices_by_multiverse_id):
	def best(considered_multiverse_ids):
		best_price = None
		best_record = None
		foil_to_regular_fallback = False
		if is_foil:
			[best_price, best_record] = multiverse_id_with_best_price(prices_by_multiverse_id, considered_multiverse_ids, lambda x : x.EUR_foil)
			if best_price is None:
				[best_price, best_record] = multiverse_id_with_best_price(prices_by_multiverse_id, considered_multiverse_ids, lambda x : x.USD_foil)
				if best_price is None:
					foil_to_regular_fallback = True
				else:
					best_price *= CONVERSION_USD_TO_EUR

		if best_price is None:
			[best_price, best_record] = multiverse_id_with_best_price(prices_by_multiverse_id, considered_multiverse_ids, lambda x : x.EUR)

		if best_price is None:
			[best_price, best_record] = multiverse_id_with_best_price(prices_by_multiverse_id, considered_multiverse_ids, lambda x : x.USD)
			if best_price is not None:
				best_price *= CONVERSION_USD_TO_EUR

		if foil_to_regular_fallback and best_price is not None:
			FOIL_PRICE_MULTIPLIER = 2.0
			best_price *= FOIL_PRICE_MULTIPLIER
		return best_price, best_record

	considered_multiverse_ids = []
	name_fallback = False
	if mcm_id in mtg_json_data.mcm_id_to_multiverse_id:
		considered_multiverse_ids = mtg_json_data.mcm_id_to_multiverse_id.get(mcm_id)
		best_price, best_record = best(considered_multiverse_ids)
		if best_price is not None:
			return best_price, best_record, False

	if not mcm_csv_name in mtg_json_data.name_to_multiverse_id:
		for x in considered_multiverse_ids:
			print(x)
		print("Missing name.")
		return None, None, None

	considered_multiverse_ids = mtg_json_data.name_to_multiverse_id.get(mcm_csv_name)
	best_price, best_record = best(considered_multiverse_ids)
	return best_price, best_record, True
	# add this as a note!
	#print("Missing price €.", print_item_info)

#TODO: recover this functionality
if __name__ == "__main__3":
	parser = argparse.ArgumentParser(description='Prepare data from mtgjson.com files. Take multiple json files and output one.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('input_files', help='in json format', nargs='*')

	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('--merge', nargs=1, help='merge to', metavar='output_file')
	group.add_argument('--list', action='store_true', help='list included multiverse_id')
	group.add_argument('--interesting', action='store_true', help='see what cards have unusual prices')

	args = parser.parse_args()

	if args.merge:
		serialize.to_file(args.merge[0], merged.values())
	if args.list:
		for (id, r) in merged.items():
			print(id)
	if args.interesting:
		interesting = []

		for r in merged.values():
			# print(r)
			if (r.USD is None or r.EUR is None):
				continue
			pln_USD = r.USD * 3.80
			pln_EUR = r.EUR * 4.32
			difference = pln_USD - pln_EUR
			relative = pln_USD / pln_EUR
			# difference *= -1.0
			# relative = 1.0 / relative
			if ((difference > 8.0 and relative > 2.0)): # or (difference > 3.0 and relative > 3.0)
				# print(r.multiverse_id, pln_USD, pln_EUR)
				interesting.append((difference, relative, r.multiverse_id, pln_USD, pln_EUR))
				# interesting.append(difference)

		interesting.sort(key = lambda x: x[1])
		interesting.reverse()
		if False:
			for i in interesting:
				print(i[0], i[1], i[2], i[3])
		else:
			ids = []
			for i in interesting:
				ids.append(i[2])
			print(json.dumps({"main":ids}))

##########################

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Prepare data from mtgjson.com files. Take multiple json files and output one.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--mtg-json', help='mtg json data file', required=True)
	parser.add_argument('--prices', help='serialized binary format', nargs='*', required=True)
	parser.add_argument('--user', help='cardmarket user data file', required=True)
	parser.add_argument('--mcm-products', help='cardmarket products data file', required=True)
	parser.add_argument('--wants', help='personal wants txt')
	parser.add_argument('--summary', help='output file name', required=True)

	# group = parser.add_mutually_exclusive_group(required=True)
	# group.add_argument('--filter', action='store_true', help='...')
	# group.add_argument('--invert', action='store_true', help='invert top level maps {key : value} => {value : [keys]}')
	# group.add_argument('--merge', action='store_true', help='merge top level maps')

	args = parser.parse_args()

	wants_set = None
	if args.wants:
		with open(args.wants) as f:
			wants_set = set(line.rstrip() for line in f)

	logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
	logging.info("Loading prices...")
	prices_by_multiverse_id = price_record.merge(args.prices)
	logging.info("Found {} prices...".format(len(prices_by_multiverse_id)))

	logging.info("Loading mtg_json...")
	mtg_json_data = mtg_json.mtg_json()
	with open(args.mtg_json, 'r') as f:
		mtg_json_data.extract(json.load(f))

	logging.info("Loading MCM items...")
	mcm_csv = dict()
	for t in cardmarket_csv_to_id_and_name(open(args.mcm_products)):
		assert t[0] not in mcm_csv
		mcm_csv[t[0]] = t

	logging.info("User...")
	deals = []
	#TODO: hardcodeed filenames
	#TODO: mcm api strings magic
	with open(args.user, 'r') as f:
		data = json.load(f)
		for d in data:
			comments = d["comments"]
			mcm_id = d["idProduct"]
			if not mcm_id in mcm_csv:
				print("%%%%%%%%%%%%%% Missing MCM product. %%%%%%%%%%%%%%%%")
				continue

			[mcm_csv_id, mcm_csv_name, mcm_csv_is_single] = mcm_csv.get(mcm_id)
			print_item_info = "{} {}".format(mcm_csv_name, mcm_csv_id)
			assert mcm_csv_id == mcm_id
			if not mcm_csv_is_single:
				print("Not MtG single.", print_item_info)
				continue

			price_eur = d["priceEUR"]
			is_foil = d["isFoil"]
			is_playset = d["isPlayset"]
			if is_playset:
				price_eur /= 4.0

			value, record, name_fallback = value_based_on_market(mcm_id, mcm_csv_name, is_foil, mtg_json_data, prices_by_multiverse_id)
			if value is None:
				print("Cannot determine value.", mcm_csv_name, mcm_id, record)
				continue
			PER_UNIT_SHIPPNG_COST = 0.1
			how_good = worth_it(value, price_eur + PER_UNIT_SHIPPNG_COST)
			wanted = (mcm_csv_name in wants_set)
			deals.append(summary.DataRow(how_good, price_eur, value, mcm_csv_name, is_foil, is_playset, wanted, name_fallback, comments, price_record.date_from_record(record).isoformat()))

	#column_names = ["HowGood", "User", "Market", "€", "foil", "4", "name", "wanted", "fallback", "comments", "date"]
	with open(args.summary, 'w') as file:
		file.write(summary.generate_summary(deals))
	if False:
		deals.sort(key=lambda x: x[0])
		info_format = "{:7.2f} {:7.2f} {:7.2f} {:40} {} {} {:30} {} {} {}"
		head_format = "{:7} {:7} {:7} {:10} {} {} {:40} {} {} {}"
		for x in deals:
			bar = cool_bar_string(40, 10.0, x[1])
			playset = "④" if x[5] else " "
			foil = "☆" if x[4] else " "
			name_fallback = "?" if x[8] else " "
			wanted = "X" if x[7] else " "
			print(info_format.format(x[0], x[1], x[2], bar, foil, playset, x[3], x[6], name_fallback, wanted, x[9]))
		print(head_format.format())
