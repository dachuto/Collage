import argparse
import datetime
import json

import serialize

def date_from_record(r):
	return datetime.datetime(r.year, r.month, r.day)

def newest(old, record):
	if date_from_record(record) > date_from_record(old):
		return record
	return old

def merge(input_files):
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

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Query data from price data.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('input_files', help='in serialized binary format', nargs='*')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('--merge', nargs=1, help='merge to', metavar='output_file')
	group.add_argument('--list', action='store_true', help='list included multiverse_id')
	group.add_argument('--interesting', action='store_true', help='see what cards have unusual prices')

	args = parser.parse_args()

	merged = merge(args.input_files)
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