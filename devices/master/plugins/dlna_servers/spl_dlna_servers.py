#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard module
import schnipsllogger
from epgprovider import EPGProvider
import defaults
from classes import MovieInfo
from messagehandler import Query
from directorymapper import DirectoryMapper
from jsonstorage import JsonStorage
import sys
import os
import time
import traceback
from datetime import datetime
from xml.dom.minidom import parseString
from urllib.parse import urlparse, unquote
import socket

# Add the directory containing your module to the Python path (wants absolute paths)
ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../../../common"))
sys.path.append(os.path.abspath(ScriptPath))

ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../.."))

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(ScriptPath))
# own local modules


class SplPlugin(EPGProvider):
	plugin_id = 'dlna_servers'
	plugin_names = ['Filmarchiv']

	def __init__(self, modref):
		''' inits the plugin
		'''
		self.modref = modref
		self.logger = schnipsllogger.getLogger(__name__)
		# do the plugin specific initialisation first
		self.origin_dir = os.path.dirname(__file__)

		# at last announce the own plugin
		super().__init__(modref)
		modref.message_handler.add_event_handler(
			self.plugin_id, 0, self.event_listener)
		modref.message_handler.add_query_handler(
			self.plugin_id, 0, self.query_handler)

		# plugin specific stuff

		self.providers = set(["DLNA"])
		# additional to our whoosh db, we need to cache the categories to not have
		# to read through the huge whoosh db at start to reconstruct the categories list again
		self.categories_storage = JsonStorage(
			self.plugin_id, 'runtime', "categories_storage.json", {'categories_storage': []})
		self.categories = self.categories_storage.read('categories_storage')

	def event_listener(self, queue_event):
		''' react on events
		'''
		#print("event handler", self.plugin_id, queue_event.type, queue_event.user)
		# for further pocessing, do not forget to return the queue event
		return queue_event

	def get_real_plugin_name(self, initial_plugin_name):
		''' helper routine, as on some epg types we need to correct the plugin name
		if this is the case, this method need to return its corrected plugin name
		'''
		return initial_plugin_name

	def get_plugin_id(self):
		return self.plugin_id

	def get_plugin_names(self):
		return self.plugin_names

	def get_categories(self):
		return self.categories

	def get_instance(self):
		return self

	def is_streamable(self):
		''' helper routine, as some EPGs are streamable (e.g. Youtube, mediathecs)
		but others are not, as there time is in the future
				'''
		return True
	
	# ------ plugin specific routines



	@staticmethod	# all the DLNA search methods are static just because to allow to use them for a standalone search
	def get_object_id(index):
		return '''
<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:ns0="urn:schemas-upnp-org:service:ContentDirectory:1" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
	<ns0:Browse>
	<ObjectID>%s</ObjectID>
	<BrowseFlag>BrowseDirectChildren</BrowseFlag>
	<Filter>*</Filter>
	</ns0:Browse>
</s:Body>
</s:Envelope>
''' % index

	@staticmethod	# all the DLNA search methods are static just because to allow to use them for a standalone search
	def parse_service(service):
		name = service.getElementsByTagName(
			'serviceType')[0].firstChild.nodeValue
		url = service.getElementsByTagName(
			'controlURL')[0].firstChild.nodeValue
		return {'name': name, 'url': url
				}

	@staticmethod	# all the DLNA search methods are static just because to allow to use them for a standalone search
	def parse_container(container):
		index = container.getAttribute('id')
		title = container.getElementsByTagName(
			'dc:title')[0].firstChild.nodeValue
		return {'index': index, 'title': title
				}

	@staticmethod	# all the DLNA search methods are static just because to allow to use them for a standalone search
	def parse_item(item):
		index = item.getAttribute('id')
		title = item.getElementsByTagName(
			'dc:title')[0].firstChild.nodeValue
		result = item.getElementsByTagName('res')[0]
		return {'index': index, 'title': title, 'size': result.getAttribute('size'), 'duration': result.getAttribute('duration'), 'bitrate': result.getAttribute('bitrate'), 'sampling': result.getAttribute('sampleFrequency'), 'channels': result.getAttribute('nrAudioChannels'), 'resolution': result.getAttribute('resolution'), 'url': result.firstChild.nodeValue
				}

	@staticmethod	# all the DLNA search methods are static just because to allow to use them for a standalone search
	def browse_location(location):
		import requests
		import os
		from xml.dom.minidom import parseString

		#location = 'http://fritz.box:49000'
		headers = {'Content-Type': 'text/xml; charset=utf-8', 'SOAPACTION': 'urn:schemas-upnp-org:service:ContentDirectory:1#Browse'
				}

		from urllib.parse import urlparse, unquote
		#result = requests.get('%s%s' % (minidlna, '/rootDesc.xml'))
		#result = requests.get('%s%s' % (location, '/MediaServerDevDesc.xml'))
		result = requests.get(location)
		# print(result.content.decode())
		try:
			root = parseString(result.content)
		except:
			return

		services = list(map(lambda service: SplPlugin.parse_service(
			service), root.getElementsByTagName('service')))
		# content = [ service for service in services if service['name'] == 'urn:schemas-upnp-org:service:ContentDirectory:1' ][0]
		for content in [service for service in services if service['name'] == 'urn:schemas-upnp-org:service:ContentDirectory:1']:
			url_elements = urlparse(location)
			request = '%s://%s%s' % (url_elements.scheme,
									url_elements.netloc, content['url'])
			# print(request, headers, get_object_id('0'))
			result = requests.post(
				request, data=SplPlugin.get_object_id('0'), headers=headers)
			# print(result.content.decode())
			root = parseString(result.content)
			result_elements = root.getElementsByTagName('Result')
			if len(result_elements) == 0:
				continue
			body = parseString(result_elements[0].firstChild.nodeValue)
			containers = list(map(lambda container: SplPlugin.parse_container(
				container), body.getElementsByTagName('container')))
			for container in containers:
				# print(container['index'], container['title'])

				result = requests.post(request, data=SplPlugin.get_object_id(
					container['index']), headers=headers)
				root = parseString(result.content)
				body = parseString(root.getElementsByTagName(
					'Result')[0].firstChild.nodeValue)
				# pretty = body.toprettyxml()
				# print(pretty)

				folders = list(map(lambda container: SplPlugin.parse_container(
					container), body.getElementsByTagName('container')))
				for folder in folders:
					# print("index:", folder['index'], folder['title'])

					result = requests.post(request, data=SplPlugin.get_object_id(
						folder['index']), headers=headers)
					root = parseString(result.content)
					body = parseString(root.getElementsByTagName(
						'Result')[0].firstChild.nodeValue)
					# pretty = body.toprettyxml()
					# print(pretty)

					items = list(map(lambda item: SplPlugin.parse_item(item),
									body.getElementsByTagName('item')))
					for item in items:
						file_url = urlparse(item['url'])
						if EPGProvider.identify_mime_type_by_extension(file_url.path) ==None: # unknown media
							continue
						category = unquote(file_url.path.split("/")[-2])
						print(item)
						'''
						print('Index', item['index'])
						print('Title', item['title'])
						print('Size', item['size'])
						print('Duration', item['duration'])
						print('Bitrate', item['bitrate'])
						print('Sampling', item['sampling'])
						print('Channels', item['channels'])
						print('Resolution', item['resolution'])
						print('Url', item['url'])
						print('----')
						'''
						yield {
							"title": item['title'],
							"duration": item['duration'],
							"url": item['url'],
							"category": category
						}

	@staticmethod	# all the DLNA search methods are static just because to allow to use them for a standalone search
	def broadcast_locations():
		import socket
		locations = set()
		msg = \
			'M-SEARCH * HTTP/1.1\r\n' \
			'HOST:239.255.255.250:1900\r\n' \
			'ST:upnp:rootdevice\r\n' \
			'MX:2\r\n' \
			'MAN:"ssdp:discover"\r\n' \
			'\r\n'

		# Set up UDP socket
		s = socket.socket(
			socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		s.settimeout(2)
		s.sendto(msg.encode(), ('239.255.255.250', 1900))

		try:
			while True:
				data, addr = s.recvfrom(65507)
				header_lines = data.split(b'\r\n')[1:]
				headers = {}
				for header_line in header_lines:
					elements = header_line.decode().split(": ", 1)
					key = elements[0]
					if len(elements) > 1:
						value = elements[1]
					else:
						value = ""
					headers[key] = value
				if "ST" in headers and "LOCATION" in headers and headers["ST"] == "upnp:rootdevice":
					locations.add(headers["LOCATION"])
		except socket.timeout:
			pass
		# for location in locations:
			# print(location)
		return locations

	def sleep(self):
		''' 
		another delay as the standard one
		'''
		time.sleep(300)

	def check_for_updates(self):

		try:
			locations=SplPlugin.broadcast_locations()
			# collect all movies first before write them to woosh to not block the db the whole time
			movies_found=[]
			for location in locations:
				movies_found.extend(SplPlugin.browse_location(location))
			if len(movies_found)==0:
				return
			with self.whoosh_ix.writer() as whoosh_writer:
				self.reset_index()
				self.categories=[]
				count = 0
				self.logger.info(f"loading movies from DLNA Servers...")

				for item in movies_found:
					print(item["category"],item["title"],item["url"])
					count += 1
					provider =list(self.providers)[0]
					category =item["category"]
					# to avoid doubles in categories, we need to check if we have that category already
					# we can not simply use a set(), because sets do not allow storage of dicts
					category_already_known=False
					for category_known in self.categories:
						if category_known["text"] == category:
							category_already_known=True
							break
					if not category_already_known:
						self.categories.append({
							'text': category,
							'value': {"type": "category", "expression": category}
						})
					plugin_name = self.plugin_names[0]
					source_type = defaults.MOVIE_TYPE_RECORD
					file_url = urlparse(item['url'])
					mime_type=  EPGProvider.identify_mime_type_by_extension(file_url.path)
					movie_info = MovieInfo(
						url=item["url"],
						mime=mime_type,
						title=item["title"],
						category=category,
						source=plugin_name,
						source_type=source_type,
						provider=provider,
						timestamp= datetime.fromtimestamp(1), # no origin date yet...
						duration=self.time_string_to_secs(item["duration"]),
						description="",
					)
					# fill the search engine
					whoosh_writer.update_document(
						source=plugin_name,
						source_type=source_type,
						provider=provider,
						title=item["title"],
						category=category,
						uri=movie_info['uri'],
						description="",
						timestamp= datetime.fromtimestamp(1), # no origin date yet...
						url=movie_info['url'],
						mime=movie_info['mime'],
						duration=movie_info['duration']
					)
					if not plugin_name in self.movies:
						self.movies[plugin_name] = {}
					# experimental: Do not save the movies in mem anymore, just in Whoosh
					# self.movies[plugin_name][movie_info['uri']]=movie_info

				self.categories_storage.write(
					'categories_storage', self.categories)
				self.logger.info(f"DLNA movie loaded, {count} entries")
		except Exception as err:
			self.logger.warning('failed to read DLNA Servers:{}'.format(traceback.format_exc()))

	def time_string_to_secs(self, time_string):
		elements = time_string.split(':')
		try:
			return int(elements[0])*3600 + int(elements[1])*60 + int(elements[2]) 
		except:
			return -1



if __name__ == '__main__':
	locations=SplPlugin.broadcast_locations()
	for location in locations:
		for item in SplPlugin.browse_location(location):
			print(item["category"],item["title"],item["url"])