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
from abc import ABCMeta, abstractmethod

# Non standard modules (install with pip)



# Add the directory containing your module to the Python path (wants absolute paths)

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
from splthread import SplThread

class EPGProvider(SplThread):
	plugin_id = 'satepg'
	plugin_names = ['SAT EPG']

	def __init__(self, modref):
		''' inits the plugin
		'''
		self.modref = modref
		super().__init__(modref.message_handler, self)
		# EPG has its own special hardwired categories

		self.categories = [
			{
				'text': 'category_day_today',
				'value': 'day:today'
			},
			{
				'text': 'category_day_tomorrow',
				'value': 'day:tomorrow'
			},
			{
				'text': 'category_time_now',
				'value': 'time:now'
			},
			{
				'text': 'category_time_evening',
				'value': 'time:evening'
			},
		]

		self.providers = set()
		self.movies = {}
		self.lock=Lock()

		self.runFlag = True

		# plugin specific stuff

	@abstractmethod
	def event_listener(self, queue_event):
		''' react on events
		'''

	def query_handler(self, queue_event, max_result_count):
		''' answers with list[] of results
		'''
		# print("query handler", self.plugin_id, queue_event.type,  queue_event.user, max_result_count)
		if queue_event.type == defaults.QUERY_AVAILABLE_SOURCES:
			return self.plugin_names
		if queue_event.type == defaults.QUERY_AVAILABLE_PROVIDERS:
			res = []
			for plugin_name in self.plugin_names:
				if plugin_name  in queue_event.params['select_source_values']: # this plugin is one of the wanted
						for provider in self.providers:
							if max_result_count > 0:
								res.append(provider)
								max_result_count -= 1
							else:
								return res  # maximal number of results reached
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
			elements = queue_event.params.split(':')
			try:
				return [self.movies[elements[0]][queue_event.params]]
			except:
				return []
		if queue_event.type == defaults.QUERY_AVAILABLE_MOVIES:
			res = []
			titles = queue_event.params['select_title'].split()
			# descriptions=queue_event.params['select_description'].split()
			description_regexs = [re.compile(r'\b{}\b'.format(				description), re.IGNORECASE) for description in queue_event.params['select_description'].split()]
			for plugin_name in self.plugin_names:
				if plugin_name in queue_event.params['select_source_values']: # this plugin is one of the wanted

					# now we need to do a dirty trick, because in our movies the entries are not store be the correct plugin name,
					# but the real data source instead, which is slighty confusing,,
					plugin_name=self.get_real_plugin_name(plugin_name)
					if plugin_name in self.movies:  # are there any movies stored for this plugin?
						with self.lock:
							for movie in self.movies[plugin_name].values():
								if movie.provider in queue_event.params['select_provider_values']:
									print('search_fails_on_categories missing!!!')
									#if self.search_fails_on_categories(movie,queue_event.params['select_categories_values'] ):
									#	continue
									if titles or description_regexs: # in case any search criteria is given
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
											movie_info=MovieInfo.movie_to_movie_info(movie,'')
											movie_info['streamable']=self.is_streamable()
											movie_info['recordable']=True
											res.append(movie_info)
											max_result_count -= 1
										else:
											return res  # maximal number of results reached
			return res
		return[]

	@abstractmethod
	def get_real_plugin_name(self,initial_plugin_name):
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
			with self.lock:
				self.check_for_updates()
			time.sleep(10)

	def _stop(self):
		self.runFlag = False

