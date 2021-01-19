import requests
import datetime
import json
import gzip
import os


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

	response = requests.get('https://us.api.blizzard.com/data/wow/connected-realm/60/auctions?namespace=dynamic-us&locale=en_US&access_token=%s' % token)
	if response.status_code != 200:
		raise Exception('Failed to get auction house data')
	data = response.json()
	return data['auctions']


def main():
	with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as f:
		conf = json.loads(f.read())

	token = create_access_token(conf['client_id'], conf['client_secret'])
	data = get_region_ah_data(token, 'Stormrage')

	with gzip.open(datetime.datetime.now().strftime('Stormrage_US-%Y-%m-%d-%H-%M.json.gz'), 'wb', 9) as f:
		f.write(json.dumps(data).encode('utf8'))


if __name__ == '__main__':
	main()
