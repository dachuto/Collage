import argparse
import json

class filter_merge:
	def __init__(self):
		self.merged = dict()

	def extract(self, data):
		for c in data["DOM"]["cards"]:
			self.merged[c["name"]] = [1]

	def done(self):
		print(json.dumps(self.merged, indent="\t", separators=(",", ":"), sort_keys=True))


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

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Prepare data from mtgjson.com files. Take multiple json files and output one.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('input_files', help='in json format', nargs='*')
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
			data = json.load(f)
			merger.extract(data)
	merger.done()