import argparse
import json
import datetime
import dataclasses

import serialize

class price_record:
	def date_from_record(r):
		return datetime.datetime(r.year, r.month, r.day)

	def merge(input_files):
		def newest(old, record):
			if date_from_record(record) > date_from_record(old):
				return record
			return old

		fresh = dict()

		for name in input_files:
			f = serialize.from_file(name)
			for record in f:
				old = fresh.get(record.multiverse_id)
				updated = old
				if old is None:
					updated = record
				else:
					updated = newest(old, record)
				fresh[record.multiverse_id] = updated
		return fresh

class filter_merge:
	def __init__(self):
		# self.merged = dict()
		self.merged = []
		self.by_name = dict()
		self.by_multiverse_id = dict()
		self.by_mcm_id = dict()

	def extract(self, data):
		for (set_name, values) in data.items():
			# x = datetime.datetime.strptime(values["releaseDate"], "%Y-%m-%d")
			for v in values["cards"]:
				name = v["name"]
				multiverse_id = v.get("multiverseId", None)
				mcm_id = v.get("mcmId", None)
				self.by_name.setdefault(name, []).append((multiverse_id, mcm_id))
				if multiverse_id is not None:
					self.by_multiverse_id.setdefault(multiverse_id, []).append((name, mcm_id))
				if mcm_id is not None:
					self.by_mcm_id.setdefault(mcm_id, []).append((name, multiverse_id))

	def done(self):
		pass
		# for (k, v) in self.by_name.items():
		# for (k, v) in self.by_multiverse_id.items():
		# for (k, v) in self.by_mcm_id.items():
		# 	print(len(v), k)

class invert_map:
	def __init__(self):
		self.merged = dict()

	def extract(self, data):
		for k, names in data.items():
			names_as_string = " // ".join(names)
			if names_as_string in self.merged:
				self.merged[names_as_string].append(k)
			else:
				self.merged[names_as_string] = [k]

	def done(self):
		print(json.dumps(self.merged))

class just_merge:
	def __init__(self):
		self.merged = dict()

	def extract(self, data):
		for k, names in data.items():
			self.merged[k] = names

	def done(self):
		print(json.dumps(self.merged))

#################################

import csv

def cardmarket_csv_to_id_and_name(f):
	r = csv.reader(f)
	next(r) # skip the first line
	for row in r:
		yield (int(row[0]), row[1], row[3] == "Magic Single")

###########################

def worth_it(market_price, individual_price):
	FLAT_PER_UNIT = 0.1
	investment = individual_price + FLAT_PER_UNIT
	profit = market_price - investment
	return profit / investment

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
#TODO: recover this functionality
if False:
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
	parser.add_argument('input_files', help='in json format', nargs='*')
	parser.add_argument('--prices', help='serialized binary format', nargs='*', required=True)
	parser.add_argument('--user', help='cardmarket user data file', required=True)
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('--filter', action='store_true', help='...')
	group.add_argument('--invert', action='store_true', help='invert top level maps {key : value} => {value : [keys]}')
	group.add_argument('--merge', action='store_true', help='merge top level maps')

	args = parser.parse_args()

	merger = None
	if args.filter:
		merger = filter_merge()
	if args.invert:
		merger = invert_map()
	if args.merge:
		merger = just_merge()

	for name in args.input_files:
		with open(name, 'r') as f:
			# pass
			data = json.load(f)
			merger.extract(data)
	merger.done()

	prices_by_multiverse_id = price_record.merge(args.prices)

	mcm_csv = dict()
	for t in cardmarket_csv_to_id_and_name(open("../content")):
		assert t[0] not in mcm_csv
		mcm_csv[t[0]] = t

	def update_considering_nones(old_price, new_price):
		if new_price is None:
			return old_price
		if old_price is None:
			return new_price
		if old_price < new_price:
			return old_price
		return new_price

	prices_by_name = dict()
	for (name, v) in merger.by_name.items():
		best_price = None
		for (multiverse_id, mcm_id) in v:
			if multiverse_id is not None:
				record = prices_by_multiverse_id.get(multiverse_id, None)
				if record is not None:
					best_price = update_considering_nones(best_price, record.EUR)
		prices_by_name[name] = best_price
		# if best_price is None:
		# 	print("NONE for ", name, v)

	prices_by_mcm_id = dict()
	for (mcm_id, v) in merger.by_mcm_id.items():
		best_price = None
		for (name, multiverse_id) in v:
			name_fallback = True
			# COPY PASTE!
			if multiverse_id is not None:
				record = prices_by_multiverse_id.get(multiverse_id, None)
				if record is not None:
					best_price = update_considering_nones(best_price, record.EUR)
					name_fallback = True # only change!
			#######
			if name_fallback:
				best_price = update_considering_nones(best_price, prices_by_name[name])
		prices_by_mcm_id[mcm_id] = best_price

	deals = []
	#TODO: hardcodeed filenames
	#TODO: mcm api strings magic
	with open(args.user, 'r') as f:
		data = json.load(f)
		for d in data:
			mcm_id = d["idProduct"]
			[mcm_csv_id, mcm_csv_name, mcm_csv_is_single] = mcm_csv.get(mcm_id)
			assert mcm_csv_id == mcm_id
			if not mcm_csv_is_single:
				print("Not MtG single:", mcm_csv_name)
				continue

			price_eur = d["priceEUR"]
			is_foil = d["isFoil"]
			is_playset = d["isPlayset"]
			if is_playset:
				price_eur /= 4.0

			market_price = prices_by_mcm_id.get(mcm_id, None)
			if market_price is None:
				print("Missing price € for", mcm_csv_name)
				continue

			if is_foil:
				FOIL_PRICE_MULTIPLIER = 4.0
				market_price *= FOIL_PRICE_MULTIPLIER

			how_good = worth_it(market_price, price_eur)
			deals.append((how_good, price_eur, market_price, mcm_csv_name, is_foil, is_playset))

	deals.sort(key=lambda x: x[0])
	for x in deals:
		bar = cool_bar_string(10, 5.0, x[1])
		playset = "④" if x[5] else " "
		foil = "☆" if x[4] else " "
		print("{:6.3f} {:7.2f} {:7.2f} {:10} {} {} {}".format(x[0], x[1], x[2], bar, foil, playset, x[3]))
