#!/usr/bin/env python

import re
import requests
from xml.etree import cElementTree as ET


class MyAnimeList:
    username = ''
    password = ''
    base_url = 'http://myanimelist.net/api'
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36'

    anime_status_names = {
        1: 'watching',
        2: 'completed',
        3: 'on hold',
        4: 'dropped',
        6: 'plan to watch'  # not a typo
    }

    manga_status_names = {
        1: 'reading',
        2: 'completed',
        3: 'onhold',
        4: 'dropped',
        6: 'plan to read'
    }

    def __init__(self, config):
        self.username = config['username']
        self.password = config['password']

    def search(self, query, s_type='manga'):
        payload = {'q': query}

        r = requests.get(
            self.base_url + '/%s/search.xml' % s_type,
            params=payload,
            auth=(self.username, self.password),
            headers={'User-Agent': self.user_agent}
        )

        if (r.status_code == 204):
            return []

        elements = ET.fromstring(r.text)
        return [dict((attr.tag, attr.text) for attr in el) for el in elements]

    def list(self, status='all', username=None, s_type='manga'):
        if username == None:
            username = self.username

        payload = {'u': username, 'status': status, 'type': s_type}
        r = requests.get(
            'http://myanimelist.net/malappinfo.php',
            params=payload,
            headers={'User-Agent': self.user_agent}
        )

        result = dict()
        try:
            for raw_entry in ET.fromstring(r.text):
                entry = dict((attr.tag, attr.text) for attr in raw_entry)

                if 'manga' == s_type and 'series_mangadb_id' in entry:
                    entry_id = int(entry['series_mangadb_id'])

                    result[entry_id] = {
                        'id': entry_id,
                        'title': entry['series_title'],
                        'read_chapters': int(entry['my_read_chapters']),
                        'status': int(entry['my_status']),
                        'score': int(entry['my_score']),
                        'read_volumes': int(entry['my_read_volumes'])
                    }
                elif 'anime' == s_type and 'series_animedb_id' in entry:
                    entry_id = int(entry['series_animedb_id'])

                    result[entry_id] = {
                        'id': entry_id,
                        'title': entry['series_title'],
                        'episode': int(entry['my_watched_episodes']),
                        'status': int(entry['my_status']),
                        'score': int(entry['my_score']),
                        'total_episodes': int(entry['series_episodes'])
                    }

        except Exception:
            result["Exception"] = "Request failed"
            return result

        return result

    def find(self, regex, status='all', username=None):
        result = []
        for key, val in self.list(status, username).items():
            if re.search(regex, val['title'], re.I):
                result.append(val)
        return result

    def update(self, item_id, entry):
        tree = ET.Element('entry')
        for key, val in entry.items():
            ET.SubElement(tree, key).text = str(val)

        encoded = ET.tostring(tree).decode('utf-8')
        xml_item = '<?xml version="1.0" encoding="UTF-8"?>' + encoded

        payload = {'data': xml_item}
        r = requests.post(
            self.base_url + '/mangalist/update/' + str(item_id) + '.xml',
            data=payload,
            auth=(self.username, self.password),
            headers={'User-Agent': self.user_agent}
        )
        return r.status_code
