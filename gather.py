import requests
import datetime
import json
import gzip
import time
import xmltodict
import shelve
import os
import argparse


def create_access_token(client_id, client_secret):
	data = {'grant_type': 'client_credentials'}
	response = requests.post('https://us.battle.net/oauth/token', data=data, auth=(client_id, client_secret))
	if response.status_code != 200:
		raise Exception('Failed to create access token')
	return response.json()['access_token']


def get_region_ah_data(token, server):
	response = requests.get('https://us.api.blizzard.com/data/wow/search/connected-realm?namespace=dynamic-us&realms.name.en_US=%s&access_token=%s' % (server, token))
	if response.status_code != 200:
		raise Exception('Failed to get realm data')
	data = response.json()
	id = data['results'][0]['data']['id']

	response = requests.get('https://us.api.blizzard.com/data/wow/connected-realm/%s/auctions?namespace=dynamic-us&locale=en_US&access_token=%s' % (id, token))
	if response.status_code != 200:
		raise Exception('Failed to get auction house data')
	data = response.json()
	return data['auctions']


def enrich_data(data, outputdir):
	t = time.time()
	with shelve.open(os.path.join(outputdir, 'itemdb')) as item_data:
		for auction in data:
			item_id = str(auction['item']['id'])
			# If we dont have the iteam data in cache download it
			if item_id not in item_data:
				response = requests.get('https://www.wowhead.com/item=%s&xml' % item_id)
				if response.status_code != 200:
					print('Failed to get item', item_id, 'data')
					continue
				idata = xmltodict.parse(response.text)['wowhead']['item']
				del idata['htmlTooltip']
				del idata['link']
				del idata['@id']
				idata['json'] = json.loads("{%s}" % idata['json'])
				if 'jsonEquip' in idata:
					idata['jsonEquip'] = json.loads("{%s}" % idata['jsonEquip'])
				item_data[item_id] = idata

			auction['ts'] = t
			#auction['item_name'] = item_data[item_id]['name']
			#if '#text' in item_data[item_id]['class']:
			#	auction['item_type'] = item_data[item_id]['class']['#text']
			#else:
			#	auction['item_type'] = item_data[item_id]['class']['@id']
	return data


def _parse_args():
	parser = argparse.ArgumentParser(description='Download WoW Auction House data')
	parser.add_argument('--server', '-s', type=str, nargs='+', default=['Stormrage'])
	parser.add_argument('--config', '-c', type=str, default=os.path.join(os.path.dirname(__file__), 'config.json'))
	parser.add_argument('--output-dir', '-o', type=str, default=os.path.join(os.path.dirname(__file__), 'data'))
	args = parser.parse_args()
	if not os.path.isdir(args.output_dir):
		os.mkdir(args.output_dir)
	return args


def main():
	args = _parse_args()
	with open(args.config, 'r') as f:
		conf = json.loads(f.read())

	for server in args.server:
		token = create_access_token(conf['client_id'], conf['client_secret'])
		data = get_region_ah_data(token, server)
		data = enrich_data(data, args.output_dir)

		# with gzip.open(os.path.join(args.output_dir, datetime.datetime.now().strftime(server + '_US-%Y-%m-%d-%H-%M.json.gz')), 'wb', 9) as f:
		with gzip.open(os.path.join(args.output_dir, server + '.json.gz'), 'ab', 9) as f:
			f.write(json.dumps(data).encode('utf8'))
			f.write(b"\n")


if __name__ == '__main__':
	main()
