#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard module
import sys
import os
import threading
import ssl
import json
from base64 import b64encode
from threading import Timer , Lock
import argparse
import time
import datetime
import calendar
import subprocess
import copy
from io import StringIO
import threading
from pprint import pprint
import lzma
import time
import urllib
from urllib.request import urlopen,urlretrieve,  urlparse, urlunparse
from xml.etree.ElementTree import parse
import re

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
		super().__init__(modref)
		modref.message_handler.add_event_handler(
		self.plugin_id, 0, self.event_listener)
		modref.message_handler.add_query_handler(
		self.plugin_id, 0, self.query_handler)


		# plugin specific stuff


	def event_listener(self, queue_event):
		''' react on events
		'''
		#print("mediathek_ard event handler", queue_event.type, queue_event.user)
		# for further pocessing, do not forget to return the queue event
		return queue_event

	def query_handler(self, queue_event, max_result_count):
		''' answers with list[] of results
		'''
		# print("query handler", self.plugin_id, queue_event.type,  queue_event.user, max_result_count)
		if queue_event.type == defaults.QUERY_AVAILABLE_SOURCES:
			return self.plugin_names
		if queue_event.type == defaults.QUERY_AVAILABLE_PROVIDERS:
			res=[]
			for plugin_name in self.plugin_names:
				if plugin_name  in queue_event.params['select_source_values']: # this plugin is one of the wanted
					for provider in self.providers:
						if max_result_count>0:
							res.append(provider)
							max_result_count-=1
						else:
							return res # maximal number of results reached
			return res
		if queue_event.type == defaults.QUERY_AVAILABLE_CATEGORIES:
			res = []
			for plugin_name in self.plugin_names:
				# this plugin is one of the wanted
				if plugin_name in queue_event.params['select_source_values']:
					for category in self.categories:
						if max_result_count > 0:
							res.append(category)
							max_result_count -= 1
						else:
							return res  # maximal number of results reached
			return res
		if queue_event.type == defaults.QUERY_MOVIE_ID:
			elements=queue_event.params.split(':')
			try:
				return [self.movies[elements[0]][queue_event.params]]
			except:
				return []
		if queue_event.type == defaults.QUERY_AVAILABLE_MOVIES:
			res=[]
			titles=queue_event.params['select_title'].split()
			#descriptions=queue_event.params['select_description'].split()
			description_regexs=[re.compile (r'\b{}\b'.format(description),re.IGNORECASE) for description in queue_event.params['select_description'].split()]
			for plugin_name in self.plugin_names:
				if plugin_name in queue_event.params['select_source_values']: # this plugin is one of the wanted

					# now we need to do a dirty trick, because in our movies the entries are not store be the correct plugin name,
					# but the real data source instead, which is slighty confusing,,
					plugin_name=self.get_real_plugin_name(plugin_name)
					if plugin_name in self.movies: # are there any movies stored for this plugin?
						with self.lock:
							for movie in self.movies[plugin_name].values():
								if movie.provider in queue_event.params['select_provider_values']:
										print('search_fails_on_categories missing!!!')
										#if self.search_fails_on_categories(movie,queue_event.params['select_categories_values'] ):
										#	continue
										if titles or description_regexs: # in case any search criteria is given
											if titles:
												found=False
												for title in titles:
													if title.lower() in movie.title.lower():
														found=True
													if title.lower() in movie.category.lower():
														found=True
												if not found:
													continue
											if description_regexs:
												found=False
												for description_regex in description_regexs:
													if re.search(description_regex, movie.description):
														found=True
												if not found:
													continue
												
											if max_result_count>0:
												movie_info=MovieInfo.movie_to_movie_info(movie,'')
												movie_info['streamable']=self.is_streamable()
												movie_info['recordable']=True
												res.append(movie_info)
												max_result_count-=1
											else:
												return res # maximal number of results reached
			return res
		return[]


	def get_real_plugin_name(self,initial_plugin_name):
		''' helper routine, as on some epg types we need to correct the plugin name
		if this is the case, this method need to return its corrected plugin name
		'''
		return initial_plugin_name

	def is_streamable(self):
		''' helper routine, as some EPGs are streamable (e.g. Youtube, mediathecs)
		but others are not, as there time is in the future
		'''
		return True

	def _run(self):
		''' starts the server
		'''
		tick = 0
		while self.runFlag:
			with self.lock:
				self.check_for_updates()
			time.sleep(10)

	def _stop(self):
		self.runFlag = False

	def time_string_to_secs(self, time_string):
		elements=time_string.split(':')
		seconds=0
		for element in elements:
			try:
				seconds=seconds*60 +int(element)
			except:
				return -1
		return seconds

	def check_for_updates(self):
		file_name=os.path.join(self.origin_dir,'online_filmlist')
		try: # does the file exist at all already?
			filmlist_time_stamp= os.path.getmtime(file_name)
		except:
			filmlist_time_stamp=0
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


		#with open('/home/steffen//Desktop/workcopies/schnipsl/Filmliste-akt') as data:
		with open(file_name) as data:
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
				new_movie.add_stream('mp4','',data_array[8])
				if not plugin_name in self.movies:
					self.movies[plugin_name]={}
				self.movies[plugin_name][new_movie.uri()]=new_movie


		print("filmlist loaded, {0} entries",count)
