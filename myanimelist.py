#!/usr/bin/env python

import re, requests
from xml.etree import cElementTree as ET

class MyAnimeList:
	username = ''
	password = ''
	base_url = 'http://myanimelist.net/api'

	status_names = {
		1: 'watching',
		2: 'completed',
		3: 'on hold',
		4: 'dropped',
		6: 'plan to watch' # not a typo
	}

	status_codes = {v:k for k,v in status_names.items()}

	def __init__(self, config):
		self.username = config['username']
		self.password = config['password']

	def search(self, query):
		payload = { 'q': query }
		r = requests.get(self.base_url + '/anime/search.xml', params=payload, auth=(self.username, self.password))
		if (r.status_code == 204):
			return []
		return [dict((attr.tag, attr.text) for attr in el) for el in ET.fromstring(r.text)]

	def list(self, status='all', username=None):
		if username == None:
			username = self.username
		payload = { 'u': username, 'status': status, 'type': 'anime' }
		r = requests.get('http://myanimelist.net/malappinfo.php', params=payload)

		result = dict()
		for raw_entry in ET.fromstring(r.text):
			entry = dict((attr.tag, attr.text) for attr in raw_entry)

			if 'series_animedb_id' in entry:
				entry_id = int(entry['series_animedb_id'])

				result[entry_id] = {
					'id': entry_id,
					'title': entry['series_title'],
					'episode': int(entry['my_watched_episodes']),
					'status': int(entry['my_status']),
					'score': int(entry['my_score']),
					'total_episodes': int(entry['series_episodes'])
				}

		return result

	def find(self, regex, status='all', username=None):
		result = []
		for key, val in self.list(status, username).items():
			if re.match(regex, val['title'], re.I):
				result.append(val)
		return result

	def update(self, item_id, entry):
		tree = ET.Element('entry')
		for key, val in entry.items():
			ET.SubElement(tree, key).text = str(val)
		xml_item = '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(tree).decode('utf-8')

		payload = { 'data': xml_item }
		r = requests.post(self.base_url + '/animelist/update/' + str(item_id) + '.xml', data=payload, auth=(self.username, self.password))
		return r.status_code
