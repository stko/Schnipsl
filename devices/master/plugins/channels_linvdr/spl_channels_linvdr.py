#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard module
from messagehandler import Query
from classes import MovieInfo
import defaults
from streamchannels import StreamChannel
import sys
import os
from base64 import b64encode
import time

from threading import  Lock
from pprint import pprint
from urllib.parse import urljoin 
import requests
import re

# Non standard modules (install with pip)

ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../common"))


# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(ScriptPath))
# own local modules
from classes import MovieInfo
from scheduler import Scheduler
from jsonstorage import JsonStorage

class SplPlugin(StreamChannel):
	plugin_id = 'channels_linvdr'
	plugin_names = ['LinVDR Live']

	def __init__(self, modref):
		''' inits the plugin
		'''
		# do the plugin specific initialisation first
		self.providers=set()
		self.movies={}
		self.origin_dir = os.path.dirname(__file__)
		self.config = JsonStorage(self.plugin_id, 'backup', "config.json", [{
			'url':'http://192.168.1.7:3000/channels.html',
				'channels_per_device':0
				}]
		)		

		# at last announce the own plugin
		super().__init__(modref)
		modref.message_handler.add_event_handler(
			self.plugin_id, 0, self.event_listener)
		modref.message_handler.add_query_handler(
			self.plugin_id, 0, self.query_handler)

	#------ plugin specific routines

	def loadChannels(self):
		for server in self.config.read('all'):
			try:
				f = requests.get(server['url'])
				content=f.text
				match = re.search(r'<ol class="items">(.*)</ol>',content,re.DOTALL)
				if match:
					lines=match.group(1).split('\n')
					item_regex=re.compile(r'<li value=".*"><a href="(.*)" vod  tvid=".*">(.*)</a>')
					plugin_name=self.plugin_names[0]
					source_type=defaults.MOVIE_TYPE_STREAM
					with self.lock:
						for line in lines:
							item_match=re.search(item_regex,line)
							if item_match:
								full_url=urljoin(server['url'],item_match.group(1))
								provider=item_match.group(2)
								self.providers.add(provider)
								new_movie = MovieInfo(
									url = full_url,
									mime = 'video/MP2T',
									title = provider+' Live',
									category = 'live',
									source = plugin_name,
									source_type = source_type,
									provider = provider,
									timestamp = 0,
									duration = 0,
									description = ''
								)

								if not plugin_name in self.movies:
									self.movies[plugin_name]={}
								self.movies[plugin_name][new_movie['uri']]=new_movie


			except Exception as e:
				print(str(e))

