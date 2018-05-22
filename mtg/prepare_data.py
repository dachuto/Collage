import argparse
import json

def extract_info_2(data):
	cards = data['cards']
	for c in cards:
		try:
			name = c['name']
		except KeyError:
			print('No name!', c)
		
		try:
			c['multiverseid']
		except KeyError:
			print('No multiverseid !', c)

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
	group.add_argument('--invert', action='store_true', help='invert top level maps {key : value} => {value : [keys]}')
	group.add_argument('--merge', action='store_true', help='merge top level maps')

	args = parser.parse_args()

	merger = None
	if args.invert:
		merger = invert_map()
	if args.merge:
		merger = just_merge()

	for name in args.input_files:
		with open(name, 'r') as f:
			data = json.load(f)
			merger.extract(data)
	merger.done()