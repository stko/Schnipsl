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
from messagehandler import Query
from classes import MovieInfo
from classes import Movie
import defaults
from epgprovider import EPGProvider

class SplPlugin(EPGProvider):
	plugin_id='mediathek_ard'
	plugin_names=['Öffi Mediathek','LiveTV']

	def __init__(self, modref):
		''' inits the plugin
		'''
		self.modref = modref

		# do the plugin specific initialisation first
		self.origin_dir = os.path.dirname(__file__)


		# at last announce the own plugin
		super().__init__(modref, self.origin_dir)
		modref.message_handler.add_event_handler(
		self.plugin_id, 0, self.event_listener)
		modref.message_handler.add_query_handler(
		self.plugin_id, 0, self.query_handler)


		# plugin specific stuff


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

	def get_plugin_names(self ):
		return self.plugin_names

	def is_streamable(self):
		''' helper routine, as some EPGs are streamable (e.g. Youtube, mediathecs)
		but others are not, as there time is in the future
		'''
		return True

	# ------ plugin specific routines

	def getAbsolutePath(self, file_name):
		return os.path.join(self.origin_dir, file_name)

	def check_for_updates(self):
		file_name=self.getAbsolutePath('online_filmlist')
		try: # does the file exist at all already?
			filmlist_time_stamp= os.path.getmtime(file_name)
		except:
			filmlist_time_stamp=0
		new_whoosh_index_is_needed=False
		if filmlist_time_stamp<time.time() - 60*60*48: # file is older as 48 hours
			print("Retrieve film list")
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
						print(url)
						print(prio)
						print()
				if url:
					try:
						urlretrieve(url,file_name+'.pack')
					except  Exception as e:
						print('failed filmlist download',str(e))
					try:
						with open(file_name,'wb') as unpack_file_handle:
							unpack_file_handle.write(lzma.open(file_name+'.pack').read())
							new_whoosh_index_is_needed=True # re-index the data
							self.reset_index() # destroy the existing index
							print('filmlist server list downloaded')
					except  Exception as e:
						print('failed filmlist unpack',str(e))
				
			except  Exception as e:
				print('failed filmlist server list download')
		else:
			if self.movies:
				return # no need to load, we have already movie data
		loader_remember_data={'provider':'','category':''}


		'''
		Bootstrap to read the filmlist:
		1. read the list of actual filmlist URLs from https://res.mediathekview.de/akt.xml
		'''
		with open(file_name) as data:
			with self.whoosh_ix.writer() as whoosh_writer:
				count=0
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
					new_movie = Movie(
						source=plugin_name,
						source_type=source_type,
						provider=provider,
						category=category,
						title=data_array[2],
						timestamp=data_array[16],
						duration=self.time_string_to_secs(data_array[5]),
						description=data_array[7],
						url=data_array[8]
					)
					# fill the search engine
					try: # livestream do not have a duration
						timestamp=datetime.datetime.fromtimestamp(int(data_array[16]))
					except:
						timestamp=None
					if new_whoosh_index_is_needed:
						whoosh_writer.update_document(
							source=plugin_name,
							provider=provider,
							title=data_array[2],
							category=category,
							uri=new_movie.uri(),
							## because of potential resource problems, we do not make the description searchable
							#description=data_array[7], 
							timestamp=timestamp
						)
					new_movie.add_stream('mp4','',data_array[8])
					if not plugin_name in self.movies:
						self.movies[plugin_name]={}
					self.movies[plugin_name][new_movie.uri()]=new_movie


		print("filmlist loaded, {0} entries",count)

	def time_string_to_secs(self, time_string):
		elements=time_string.split(':')
		seconds=0
		for element in elements:
			try:
				seconds=seconds*60 +int(element)
			except:
				return -1
		return seconds

