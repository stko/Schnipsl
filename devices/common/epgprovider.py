#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard module


from classes import MovieInfo
import defaults
from splthread import SplThread
import sys
import os
from base64 import b64encode
from threading import Timer, Lock
import time
from pprint import pprint
import time
from urllib.request import urlopen, urlretrieve,  urlparse, urlunparse
from xml.etree.ElementTree import parse
import json
from abc import abstractmethod


# Non standard modules (install with pip)
from whoosh import index
from whoosh.fields import *
from whoosh.qparser import MultifieldParser, QueryParser
from whoosh.qparser.dateparse import DateParserPlugin

# Add the directory containing your module to the Python path (wants absolute paths)

ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../.."))

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(ScriptPath))

# own local modules
from directorymapper import DirectoryMapper

class EPGProvider(SplThread):

	def __init__(self, modref):
		''' inits the plugin
		'''
		self.modref = modref
		super().__init__(modref.message_handler, self)
		self.providers = set()
		self.movies = {}
		self.lock = Lock()

		self.runFlag = True
		# init the search engine
		self.whoosh_schema = Schema(
			source=KEYWORD(stored=True),
			provider=KEYWORD(stored=True),
			title=TEXT(stored=True),
			category=TEXT(stored=True),
			uri=ID(stored=True, unique=True),
			url=STORED,
			mime=STORED,
			duration=STORED,
			source_type=STORED,
			description=STORED,
			timestamp=DATETIME(stored=True)
		)
		self.index_dir = DirectoryMapper.abspath(self.get_plugin_id(), 'runtime','indexdir', True)
		if not os.path.exists(self.index_dir):
			os.mkdir(self.index_dir)
		if index.exists_in(self.index_dir):
			self.whoosh_ix = index.open_dir(self.index_dir)
		else:
			self.reset_index()  # creates a new index
		#self.whoosh_writer = self.whoosh_ix.writer()
		# plugin specific stuff

	def reset_index(self):
		# used to reset an existing index by creating it again
		self.whoosh_ix = index.create_in(self.index_dir, self.whoosh_schema)

	def is_empty(self):
		# tells if the actual db is empty
		return self.whoosh_ix.is_empty()

	@abstractmethod
	def event_listener(self, queue_event):
		''' react on events
		'''

	@abstractmethod
	def get_plugin_id(self):
		''' 
		get child class plugin id
		'''

	@abstractmethod
	def get_plugin_names(self):
		''' 
		get child class plugin name
		'''

	@abstractmethod
	def get_categories(self):
		''' 
		get child class categories
		'''

	@abstractmethod
	def get_instance(self):
		''' 
		get child class instance
		'''

	def query_handler(self, queue_event, max_result_count):
		''' answers with list[] of results
		'''
		# print("query handler", self.get_plugin_names(), queue_event.type,  queue_event.user, max_result_count)
		if queue_event.type == defaults.QUERY_AVAILABLE_SOURCES:
			return self.get_plugin_names()
		if queue_event.type == defaults.QUERY_AVAILABLE_PROVIDERS:
			res = []
			for plugin_name in self.get_plugin_names():
				# this plugin is one of the wanted
				if plugin_name in queue_event.params['select_source_values']:
					for provider in self.providers:
						if max_result_count > 0:
							res.append(provider)
							max_result_count -= 1
						else:
							return res  # maximal number of results reached
			return res
		if queue_event.type == defaults.QUERY_AVAILABLE_CATEGORIES:
			res = []
			for plugin_name in self.get_plugin_names():
				# this plugin is one of the wanted
				if plugin_name in queue_event.params['select_source_values']:
					for category in self.get_categories():
						if max_result_count > 0:
							res.append(category)
							max_result_count -= 1
						else:
							return res  # maximal number of results reached
			return res
		if queue_event.type == defaults.QUERY_MOVIE_ID:
			elements = queue_event.params.split(':') # split the uri given in queue_event.params
			res = []
			if not elements[0] in self.get_plugin_names():
				# its not our source
				pass # return res
			with self.whoosh_ix.searcher() as searcher:
				qp = QueryParser('uri', schema=self.whoosh_ix.schema)
				q = qp.parse('"'+queue_event.params+'"')
				results = searcher.search(q)
				for result in results:
					try:
						#movie_info = self.movies[result['source']][result['uri']]
						movie_info = MovieInfo(
							url = result['url'],
							mime = result['mime'],
							title = result['title'],
							category = result['category'],
							source = result['source'],
							source_type = result['source_type'],
							provider = result['provider'],
							# caution: when using timestamp(), it needs to be converted to int, otherways it will be a float
							timestamp = int(result['timestamp'].timestamp()),
							duration = result['duration'],
							description = result['description'],
							uri=result['uri']
						)
						movie_info['streamable'] = self.is_streamable()
						movie_info['recordable'] = True
						res.append(movie_info)
					except Exception as e:
						print('Exception in', self.get_plugin_names(),self.movies.keys(),result['source'],result['uri'], str(e))

			return res
		if queue_event.type == defaults.QUERY_AVAILABLE_MOVIES:
			res = []
			intersection_list = [value for value in self.get_plugin_names() if value in  queue_event.params['select_source_values']]
			if not intersection_list:
				return res
			with self.whoosh_ix.searcher() as searcher:
				# qp = QueryParser('title', schema=self.whoosh_ix.schema)
				qp = MultifieldParser(
					['title', 'category', 'timestamp'], schema=self.whoosh_ix.schema)
				query_string = ''
				if queue_event.params['select_provider_values']:
					# add a quote around each provider to make e.g. ZDF HD => 'ZDF HD' and add provider: to it
					quoted_values = map(
						lambda pr: 'provider:\''+pr+'\'', queue_event.params['select_provider_values'])
					query_string +='(' + ' OR '.join(quoted_values) + ')'
				if queue_event.params['select_category_values']:
					# now we need to build a timestamp query string, which ANDs the different time/day parameters
					timestamp_queries_unsorted={}
					for category_query in queue_event.params['select_category_values']:
						try:
							category_query_type=category_query["type"]
							if not category_query_type in timestamp_queries_unsorted:
								timestamp_queries_unsorted[category_query_type]=set()
							timestamp_queries_unsorted[category_query_type].add(category_query["expression"])
						except:
							self.get_instance().logger.warning('malformed category received:',category_query)
					# after we jave sorted the expressions, we need to make a proper query string out of it
					type_queries={}
					for type, expressions in timestamp_queries_unsorted.items():
					# first we OR each category for itself
						if type == "daytime":
							type_queries[type]='(' +' OR '.join(map(lambda pr: 'timestamp:'+pr, expressions)) + ')'
						if type == "category":
							type_queries[type]='(' +' OR '.join(map(lambda pr: 'category:'+pr, expressions)) + ')'
					# then we AND each different type
					type_query='(' +' AND '.join( type_queries.values()) + ')'
					if query_string:
						query_string+=' AND '
					query_string += type_query
					qp.add_plugin(DateParserPlugin())
				try: # if select_searchtext is empty in the browser, it will be not set in the JSON message and can cause an key exeption here, so we have to catch that!
					query_string += ' ' + queue_event.params['select_searchtext']
				except:
					pass
				q = qp.parse(query_string)
				results = searcher.search(q,limit=max_result_count, sortedby='timestamp')
				for result in results:
					try:
						#movie_info = self.movies[result['source']][result['uri']]

						movie_info = MovieInfo(
							url = result['url'],
							mime = result['mime'],
							title = result['title'],
							category = result['category'],
							source = result['source'],
							source_type = result['source_type'],
							provider = result['provider'],
							# caution: when using timestamp(), it needs to be converted to int, otherways it will be a float
							timestamp = int(result['timestamp'].timestamp()),
							duration = result['duration'],
							description = result['description'],
							uri=result['uri']
						)



						movie_info['streamable'] = self.is_streamable()
						movie_info['recordable'] = True
						res.append(movie_info)
					except Exception as e:
						print('Exception in', self.get_plugin_names(),self.movies.keys(),result['source'],result['uri'], str(e))
				return res
		return[]

	@abstractmethod
	def get_real_plugin_name(self, initial_plugin_name):
		''' helper routine, as on some epg types we need to correct the plugin name
		if this is the case, this method need to return its corrected plugin name
		'''

	@abstractmethod
	def is_streamable(self):
		''' helper routine, as some EPGs are streamable (e.g. Youtube, mediathecs)
		but others are not, as there time is in the future
		'''

	def sleep(self):
		''' 
		this method shall be overridden by childs if another delay behaviour is needed
		'''
		time.sleep(10)

	def _run(self):
		''' starts the server
		'''
		tick = 0
		while self.runFlag:
			self.check_for_updates()
			try:
				self.sleep() # does the implementation has an own sleep() method?
			except: # if not, then
				time.sleep(10)

	def _stop(self):
		self.runFlag = False

	@abstractmethod
	def check_for_updates(self):
		'''Does the regular updates.

		Make sure that self.lock() is called for single atom modify operations,
		but now for whole long running operations

		'''

	def identify_mime_type_by_extension(file_name, allowed_mime_types={
		".flv" : "video/x-flv", # Flash
		".mp4" : "video/mp4", # MPEG-4
		".m3u8" : "application/x-mpegURL", # iPhone Index
		".ts" : "video/MP2T", # iPhone Segment
		".3gp" : "video/3gpp", # 3GP Mobile
		".mov" : "video/quicktime", # QuickTime
		".avi" : "video/x-msvideo", # A/V Interleave
		".wmv" : "video/x-ms-wmv", # Windows Media
	}): 	#  static just because to allow to use them for a standalone use
		'''Identifies allowed mime types

		Make sure that self.lock() is called for single atom modify operations,
		but now for whole long running operations

		'''
		file_extension = os.path.splitext(
			file_name)[1].lower()
		if file_extension not in allowed_mime_types:
			return None
		return allowed_mime_types[file_extension]