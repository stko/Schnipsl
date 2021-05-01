#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard module
from messagehandler import Query
from classes import MovieInfo
import defaults
from splthread import SplThread
import sys
import os
import threading
import ssl
import json
from base64 import b64encode
import argparse
import time
import copy
from io import StringIO
from threading import  Lock
import uuid
from pprint import pprint
from urllib.parse import urljoin 
import requests
import re
from abc import abstractmethod

# Non standard modules (install with pip)

ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../common"))


# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(ScriptPath))
# own local modules
from classes import MovieInfo
from scheduler import Scheduler

class StreamChannel(SplThread):
	plugin_id = 'channels_satip'
	plugin_names = ['SatIP Live']

	def __init__(self, modref):
		''' creates the simulator
		'''
		self.modref = modref

		super().__init__(modref.message_handler, self)
		self.runFlag = True

		# plugin specific stuff
		self.providers=set()
		self.movies={}
		self.lock=Lock()

	def event_listener(self, queue_event):
		''' try to send simulated answers
		'''
		# for further pocessing, do not forget to return the queue event
		return queue_event

	def query_handler(self, queue_event, max_result_count):
		''' answers with list[] of results
		'''
		# print(self.plugin_id, "query handler", queue_event.type, queue_event.user, max_result_count)
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
			# just do nothing, the mediathek does not have categories
			pass
		if queue_event.type == defaults.QUERY_MOVIE_ID:
			elements=queue_event.params.split(':')
			try:
				return [self.movies[elements[0]][queue_event.params]]
			except:
				return []
		if queue_event.type == defaults.QUERY_AVAILABLE_MOVIES:
			res=[]
			try: # if select_searchtext is empty in the browser, it will be not set in the JSON message and can cause an key exeption here, so we have to catch that!
				titles=queue_event.params['select_searchtext'].split()
			except:
				titles=[]
			for plugin_name in self.plugin_names:
				if plugin_name in queue_event.params['select_source_values']: # this plugin is one of the wanted
					if plugin_name in self.movies: # are there any movies stored for this plugin?
						for movie_info in self.movies[plugin_name].values():
							if movie_info['provider'] in queue_event.params['select_provider_values']:
								
								''' special for live streams: we have just one single live stream to report,

								so we skip the whole search and store the movie directly


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
									

								'''



								if max_result_count>0:
									movie_info['streamable']=True
									movie_info['recordable']=False
									res.append(movie_info)
									max_result_count-=1
								else:
									return res # maximal number of results reached
			return res
		return[]

	def _run(self):
		''' starts the server
		'''

		scheduler = Scheduler(
			[(self.loadChannels, -60)])
		while self.runFlag:
			scheduler.execute()
			time.sleep(10)


	def _stop(self):
		self.runFlag = False

	#------ plugin specific routines

		@abstractmethod
		def loadChannels(self):
			'''load the channnels
			'''
