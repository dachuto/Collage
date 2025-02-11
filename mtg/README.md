# Tools for processing MtG cards data

We download card data in json format. See: nginx setup and install components.

## scryfall_download.py

Script to download all images from scryfall. Reasonable resolution is less than 10GB in total.

Download the latest bulk data:
```
https://scryfall.com/docs/api/bulk-data
```

```
python3 ../Collage/mtg/python_tooling/scryfall_download.py ~/Downloads/unique-artwork-.json
```

Then one can host a simple webserver with all the images:
```
python3 -m http.server 2345
```

## prepare_data.py

Takes json data as input and can output different useful information. Such as list of all english cards multiverse_ids. Now also takes a lot of market price data. Still lots of todo.

## prices_download.py

Goes to free scryfall API and gets cards prices. Saves data to custom binary file format on exit. Takes multiverse_ids from stdin.

## cardmarket_data.py

Downloads data file with all products (as .gz).
Queries all articles from specified user.

## TODO examples

```
sort multiverse_ids.txt covered_ids.txt covered_ids.txt | uniq -u | sort -n > not_covered.txt
cat not_covered.txt |  python3 prices_download.py

```

* [mtg json](mtgjson.com) - card data in json
* [scryfall](scryfall.com) - better gatherer
* [cardmarket](cardmarket.com)
