import argparse
import json
import logging
import os
import urllib.request
import time

def create_directory_if_not_exists(directory):
	if not os.path.exists(directory):
		os.makedirs(directory)

def check_file_exists(file_path):
	return os.path.exists(file_path)

def download_umage_url(url, filename):
	urllib.request.urlretrieve(url, filename)

def handle_card(obj):
	folder = obj["set"]
	file = obj["collector_number"]
	file_path = os.path.join(folder, file)
	debug_message = f"{obj['name']} - {obj['set_name']} - {file_path}"

	if not obj["highres_image"] and folder != "ltr":
		logging.info(debug_message + " no high resolution image available")
		return

	if "paper" not in set(obj["games"]):
		logging.info(debug_message + " skipping")
		return

	if check_file_exists(file_path):
		logging.info(debug_message + " already exists")
		return

	create_directory_if_not_exists(folder)
	image_url = None
	quality = "large" # png s are a bit better but much bigger in size

	if "image_uris" not in obj:
		image_url = obj["card_faces"][0]["image_uris"][quality]
	else:
		image_url = obj["image_uris"][quality]

	logging.info(debug_message + " downloading " + image_url)
	download_umage_url(image_url , file_path)
	SCRYFALL_RATE_LIMIT_SLEEP = 0.12 # https://scryfall.com/docs/api
	time.sleep(SCRYFALL_RATE_LIMIT_SLEEP)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Prepare data from mtgjson.com files. Take multiple json files and output one.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('scryfall_bulk', help='see https://scryfall.com/docs/api/bulk-data')
	args = parser.parse_args()

	logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
	# print(args)

	with open(args.scryfall_bulk) as file:
		data = json.load(file)

		for obj in data:
			handle_card(obj)