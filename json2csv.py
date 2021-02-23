import argparse
import json
import csv
import gzip
import shelve
import os


def convert(jsonfile, itemdb):
	if jsonfile.endswith('json.gz'):
		newname = jsonfile[:-7] + 'csv'
		fo = gzip.open
	elif jsonfile.endswith('json'):
		newname = jsonfile[:-4] + 'csv'
		fo = open
	else:
		raise Exception("Unknown file extension on %s" % jsonfile)

	if itemdb.endswith(".bak") or itemdb.endswith(".dat") or itemdb.endswith(".dir"):
		itemdb = itemdb[:-4]

	with fo(jsonfile, 'r') as f:
		for line in f:
			data = json.loads(line)
			fields = ['id', 'item_name', 'item_type', 'time_left', 'quantity', 'buyout', 'unit_price']
			with shelve.open(itemdb) as item_data:
				for auction in data:
					item_id = str(auction['item']['id'])
					del auction['item']['id']
					auction['item_id'] = item_id
					auction['item_name'] = item_data[item_id]['name']
					if '#text' in item_data[item_id]['class']:
						auction['item_type'] = item_data[item_id]['class']['#text']
					else:
						auction['item_type'] = item_data[item_id]['class']['@id']
					for k in auction:
						if k not in fields:
							fields.append(k)

			if os.path.exists(newname):
				with open(newname, 'a', newline='') as f:
					writer = csv.DictWriter(f, fields)
					writer.writerows(data)
			else:
				with open(newname, 'a', newline='') as f:
					writer = csv.DictWriter(f, fields)
					writer.writeheader()
					writer.writerows(data)


def _parse_args():
	parser = argparse.ArgumentParser(description='Convert Auction House JSON into a CSV')
	parser.add_argument('itemdb')
	parser.add_argument('jsonfile', nargs='+')
	return parser.parse_args()


def main():
	args = _parse_args()
	for f in args.jsonfile:
		convert(f, args.itemdb)


if __name__ == '__main__':
	main()
