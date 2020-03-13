# Tools for processing MtG cards data

We download card data in json format. See: nginx setup and install components.

## prepare_data.py

Takes json data as input and can output different useful information. Such as list of all english cards multiverse_ids.

## prices_download.py

Goes to free scryfall API and gets cards prices. Saves data to custom binary file format on exit. Takes multiverse_ids from stdin.

## query.py

Takes price binary data files as input and merges them, prints as text or most importantly computes good deals.

## TODO examples

```
python3 query.py --merge data data new
python3 query.py --list data > covered_ids.txt
sort multiverse_ids.txt covered_ids.txt covered_ids.txt | uniq -u | sort -n > not_covered.txt
cat not_covered.txt |  python3 prices_download.py

```

* [mtg json](mtgjson.com) - card data in json
* [scryfall](scryfall.com) - better gatherer

