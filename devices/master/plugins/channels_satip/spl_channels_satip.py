#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard module
from messagehandler import Query
from classes import MovieInfo
import defaults
from splthread import SplThread
import sys
import os
from base64 import b64encode

from pprint import pprint
import requests
import xmltodict
from urllib.parse import urlparse, urlunparse


# Non standard modules (install with pip)

ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../common"))


# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(ScriptPath))
# own local modules
from classes import MovieInfo
from scheduler import Scheduler
from streamchannels import StreamChannel
from jsonstorage import JsonStorage

class SplPlugin(StreamChannel):
	plugin_id = 'channels_satip'
	plugin_names = ['SatIP Live']

	def __init__(self, modref):
		''' inits the plugin
		'''
		# do the plugin specific initialisation first
		self.origin_dir = os.path.dirname(__file__)
		self.config = JsonStorage(os.path.join(
			self.origin_dir, "config.json"), {
				'channel_files': ['Astra_19.2.xspf'],
				'scheme': 'http',
				'netloc': '192.168.1.99'
			}
		)

		# at last announce the own plugin
		super().__init__(modref)
		modref.message_handler.add_event_handler(
			self.plugin_id, 0, self.event_listener)
		modref.message_handler.add_query_handler(
			self.plugin_id, 0, self.query_handler)

	def add_movie(self,provider, full_url):
		plugin_name=self.plugin_names[0]
		source_type=defaults.MOVIE_TYPE_STREAM
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



	def load_xspf(self, file_name):
		try:
			with open( file_name ) as fd:
				root = xmltodict.parse(fd.read())
				for track in root['playlist']['trackList']['track']:
					provider=track['title']
					#print (track['album'])
					location=track['location']
					url_st=urlparse(location)
					full_url = urlunparse((
							#url_st.scheme,
							self.config.read('scheme'),
							#url_st.netloc,
							self.config.read('netloc'),
							url_st.path,
							url_st.params,
							url_st.query,
							url_st.fragment,
					))
					#print(full_url)
					self.add_movie(provider, full_url)
		except Exception as e:
			print(str(e))

	def load_m3u(self, file_name):
		try:
			with open( file_name ) as fd:
				line=fd.readline()
				while line: # if not eol 
					line=line.strip()
					if line.upper().startswith('#EXTINF:'):
						try:
							provider=line.split(maxsplit=1)[1]
							location=fd.readline().strip()
							if location: # if not eol 
								url_st=urlparse(location)
								full_url = urlunparse((
										#url_st.scheme,
										self.config.read('scheme'),
										#url_st.netloc,
										self.config.read('netloc'),
										url_st.path,
										url_st.params,
										url_st.query,
										url_st.fragment,
								))
								#print(full_url)
								self.add_movie(provider, full_url)
						except:
							print('mailformed m3u element {0}'.format())
					line=fd.readline()

		except Exception as e:
			print(str(e))

	def loadChannels(self):
		for channel_file in self.config.read('channel_files'):
			full_file_path=os.path.join( self.origin_dir,channel_file)
			filename, file_extension = os.path.splitext(full_file_path)
			if file_extension.lower()=='.xspf':
				self.load_xspf(full_file_path)
			if file_extension.lower()=='.m3u':
				self.load_m3u(full_file_path)
