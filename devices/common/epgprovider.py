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
import re
from abc import abstractmethod


# Non standard modules (install with pip)
from whoosh import index
from whoosh.fields import *
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.qparser.dateparse import DateParserPlugin

# Add the directory containing your module to the Python path (wants absolute paths)

ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../.."))

# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(ScriptPath))

# own local modules


class EPGProvider(SplThread):

	def __init__(self, modref, child_dir):
		''' inits the plugin
		'''
		self.modref = modref
		super().__init__(modref.message_handler, self)
		self.providers = set()
		self.movies = {}
		self.lock = Lock()

		self.runFlag = True
		# init the search engine
		self.whoosh_schema = Schema(source=TEXT(stored=True), provider=TEXT, title=TEXT, category=TEXT, uri=ID(
			stored=True, unique=True), description=TEXT, timestamp=DATETIME)
		self.index_dir = os.path.join(child_dir, 'indexdir')
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

	@abstractmethod
	def event_listener(self, queue_event):
		''' react on events
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
			elements = queue_event.params.split(':')
			try:
				return [self.movies[elements[0]][queue_event.params]]
			except:
				return []
		if queue_event.type == defaults.QUERY_AVAILABLE_MOVIES:
			res = []
			if not self.get_plugin_names()[0] in queue_event.params['select_source_values']:
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
					# add a quote around each category to make e.g. ZDF HD => 'ZDF HD' and add timestamp: to it
					quoted_values = map(
						lambda pr: 'timestamp:'+pr, queue_event.params['select_category_values'])
					# query_string += 'timestamp:('+' '.join(quoted_values)+') '
					if query_string:
						query_string+=' AND '
					query_string += '(' +' OR '.join(quoted_values) + ')'
					qp.add_plugin(DateParserPlugin())
				query_string += ' ' + queue_event.params['select_title']
				q = qp.parse(query_string)
				results = searcher.search(q)
				for result in results:
					try:
						movie = self.movies[result['source']][result['uri']]
						movie_info = MovieInfo.movie_to_movie_info(movie, '')
						movie_info['streamable'] = self.is_streamable()
						movie_info['recordable'] = True
						res.append(movie_info)
					except Exception as e:
						print('Exception in', self.get_plugin_names()[0], e)
				return res
			titles = queue_event.params['select_title'].split()
			# descriptions=queue_event.params['select_description'].split()
			description_regexs = [re.compile(r'\b{}\b'.format(
				description), re.IGNORECASE) for description in queue_event.params['select_description'].split()]
			for plugin_name in self.get_plugin_names():
				# this plugin is one of the wanted
				if plugin_name in queue_event.params['select_source_values']:

					# now we need to do a dirty trick, because in our movies the entries are not store be the correct plugin name,
					# but the real data source instead, which is slighty confusing,,
					plugin_name = self.get_real_plugin_name(plugin_name)
					if plugin_name in self.movies:  # are there any movies stored for this plugin?
						with self.lock:
							for movie in self.movies[plugin_name].values():
								if movie.provider in queue_event.params['select_provider_values']:
									print('search_fails_on_categories missing!!!')
									# if self.search_fails_on_categories(movie,queue_event.params['select_categories_values'] ):
									#	continue
									if titles or description_regexs:  # in case any search criteria is given
										if titles:
											found = False
											for title in titles:
												if title.lower() in movie.title.lower():
													found = True
												if title.lower() in movie.category.lower():
													found = True
											if not found:
												continue
										if description_regexs:
											found = False
											for description_regex in description_regexs:
												if re.search(description_regex, movie.description):
													found = True
											if not found:
												continue

										if max_result_count > 0:
											movie_info = MovieInfo.movie_to_movie_info(
												movie, '')
											movie_info['streamable'] = self.is_streamable(
											)
											movie_info['recordable'] = True
											res.append(movie_info)
											max_result_count -= 1
										else:
											return res  # maximal number of results reached
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

	def _run(self):
		''' starts the server
		'''
		tick = 0
		while self.runFlag:
			self.check_for_updates()
			time.sleep(10)

	def _stop(self):
		self.runFlag = False

	@abstractmethod
	def check_for_updates(self):
		'''Does the regular updates.

		Make sure that self.lock() is called for single atom modify operations,
		but now for whole long running operations

		'''
