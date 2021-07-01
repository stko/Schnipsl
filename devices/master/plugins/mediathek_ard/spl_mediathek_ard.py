#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard module
import sys
import os
import time
import datetime
import lzma
import time
from urllib.request import urlopen,urlretrieve,  urlparse, urlunparse
from xml.etree.ElementTree import parse

# Non standard modules (install with pip)

# sudo apt install libyajl-dev
# sudo pip3 install jsonslicer

from jsonslicer import JsonSlicer
# Add the directory containing your module to the Python path (wants absolute paths)
ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../../../common"))
sys.path.append(os.path.abspath(ScriptPath))

ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../.."))

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(ScriptPath))
# own local modules

from jsonstorage import JsonStorage
from directorymapper import DirectoryMapper
from messagehandler import Query
from classes import MovieInfo
import defaults
from epgprovider import EPGProvider
import schnipsllogger

class SplPlugin(EPGProvider):
	plugin_id='mediathek_ard'
	plugin_names=['Öffi Mediathek','LiveTV']

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
		# each EPG has its own special hardwired categories

		self.categories = [
			{
				'text': 'category_last_week',
				'value': '{"type": "day", "expression": "[\'-1 week\' to now]"}'
			},
			{
				'text': 'category_last_month',
				'value': '{"type": "day", "expression": "[\'-4 week\' to now]"}'
			},
		]
		# additional to our whoosh db, we need to cache the providers to not have
		# to read through the huge whoosh db at start to reconstruct the provider list again
		self.provider_storage = JsonStorage(self.plugin_id, 'runtime', "provider_cache.json", {'provider_cache':[]})
		self.providers = set(self.provider_storage.read('provider_cache'))



	def event_listener(self, queue_event):
		''' react on events
		'''
		#print("event handler", self.plugin_id, queue_event.type, queue_event.user)
		# for further pocessing, do not forget to return the queue event
		return queue_event

	def get_real_plugin_name(self,initial_plugin_name):
		''' helper routine, as on some epg types we need to correct the plugin name
		if this is the case, this method need to return its corrected plugin name
		'''
		return initial_plugin_name

	def get_plugin_id(self ):
		return self.plugin_id

	def get_plugin_names(self ):
		return self.plugin_names

	def get_categories(self ):
		return self.categories

	def get_instance(self):
		return self

	def is_streamable(self):
		''' helper routine, as some EPGs are streamable (e.g. Youtube, mediathecs)
		but others are not, as there time is in the future
		'''
		return True

	# ------ plugin specific routines

	def check_for_updates(self):
		file_name='online_filmlist'
		filmlist_time_stamp= self.provider_storage.read('filmlist_time_stamp',0)
		if not filmlist_time_stamp:
			full_file_name=DirectoryMapper.abspath(self.plugin_id, 'tmpfs',file_name, True)
			try: # does the file exist at all already?
				filmlist_time_stamp= DirectoryMapper.getmtime(self.plugin_id, 'tmpfs',file_name)
			except:
				filmlist_time_stamp=0
		if filmlist_time_stamp<time.time() - 60*60*48: # file is older as 48 hours
			'''
			Bootstrap to read the filmlist:
			1. read the list of actual filmlist URLs from https://res.mediathekview.de/akt.xml
			'''
			self.logger.info("Retrieve film list")
			try:
				var_url = urlopen('https://res.mediathekview.de/akt.xml')
				server_list = parse(var_url)
				print(server_list)
				url=None
				prio=999 # dummy start value
				for item in server_list.iterfind('Server'):
					this_prio = int(item.findtext('Prio'))
					if this_prio< prio: # filter for the server with the lowest prio
						prio=this_prio
						url = item.findtext('URL')
						self.logger.info(f'Mediathek filmlist url {url}')
				if url:
					try:
						urlretrieve(url,full_file_name+'.pack')
						self.logger.info("filmlist downloaded")
					except  Exception as e:
						self.logger.warning(f'failed filmlist download {str(e)}')
					try:
						with DirectoryMapper.open(self.plugin_id, 'tmpfs',file_name,'wb') as unpack_file_handle:
							with lzma.open(DirectoryMapper.open(self.plugin_id, 'tmpfs',file_name+'.pack','rb')) as archive_file_handle:
								bytes = archive_file_handle.read(4096)
								while bytes:
									unpack_file_handle.write(bytes)
									bytes = archive_file_handle.read(4096)
							self.reset_index() # destroy the existing index
							self.provider_storage.write('filmlist_time_stamp',time.time())
							self.logger.info('filmlist server list unpacked')
					except  Exception as e:
						print('failed filmlist unpack',str(e))
			except  Exception as e:
				print('failed filmlist server list download')
		else:
			if not self.is_empty() and self.providers:
				return # no need to load, we have already movie data
		loader_remember_data={'provider':'','category':''}

		try:
			with DirectoryMapper.open(self.plugin_id, 'tmpfs',file_name) as data:
				self.reset_index()
				with self.whoosh_ix.writer() as whoosh_writer:
					count=0
					self.logger.info(f"loading filmlist...")
					for liste in JsonSlicer(data, ('X'), path_mode='map_keys'):
						count+=1
						data_array=liste[1]
						# "Sender"	0,
						# "Thema" 	1,
						# "Titel"	2,
						# "Datum"	3,
						# "Zeit"	4,
						# "Dauer"	5,
						# "Größe [MB]"	6,
						# "Beschreibung"	7,
						# "Url"				8,
						# "Website"			9,
						# "Url Untertitel"	10,
						# "Url RTMP"		11,
						# "Url Klein"		12,
						# "Url RTMP Klein"	13,
						# "Url HD"			14,
						# "Url RTMP HD"		15,
						# "DatumL"			16,
						# "Url History"		17,
						# "Geo"				18,
						# "neu"				19
						provider=data_array[0]
						category=data_array[1]
						if provider:
							loader_remember_data['provider']=provider
						else:
							provider=loader_remember_data['provider']
						if category:
							loader_remember_data['category']=category
						else:
							category=loader_remember_data['category']
						if category=='Livestream':
							source_type=defaults.MOVIE_TYPE_STREAM
							plugin_name=self.plugin_names[1]
							provider=provider.replace('Livestream','').strip()
							#print("Livestream")
						else:
							plugin_name=self.plugin_names[0]
							source_type=defaults.MOVIE_TYPE_RECORD
						self.providers.add(provider)
						try: # livestream do not have a duration
							timestamp=int(data_array[16])
							timestamp_datetime=datetime.datetime.fromtimestamp(timestamp)
						except:
							timestamp=1
							timestamp_datetime=datetime.datetime.fromtimestamp(timestamp)
						movie_info = MovieInfo(
							url = data_array[8],
							mime = 'video/mp4',
							title = data_array[2],
							category = category,
							source = plugin_name,
							source_type = source_type,
							provider = provider,
							timestamp = timestamp,
							duration = self.time_string_to_secs(data_array[5]),
							description = data_array[7],
						)
						# fill the search engine
						whoosh_writer.update_document(
							source=plugin_name,
							source_type = source_type,
							provider=provider,
							title=data_array[2],
							category=category,
							uri=movie_info['uri'],
							description=data_array[7], 
							timestamp=timestamp_datetime,
							url=movie_info['url'],
							mime=movie_info['mime'],
							duration=movie_info['duration']
						)
						if not plugin_name in self.movies:
							self.movies[plugin_name]={}
						# experimental: Do not save the movies in mem anymore, just in Whoosh
						#self.movies[plugin_name][movie_info['uri']]=movie_info

				self.provider_storage.write('provider_cache',list(self.providers))
				self.logger.info(f"filmlist loaded, {count} entries")
		except  Exception as  err:
			self.logger.warning(f'failed to read filmlist:{err}')

	def time_string_to_secs(self, time_string):
		elements=time_string.split(':')
		seconds=0
		for element in elements:
			try:
				seconds=seconds*60 +int(element)
			except:
				return -1
		return seconds

