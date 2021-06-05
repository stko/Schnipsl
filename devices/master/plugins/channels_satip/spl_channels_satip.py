#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard module
from messagehandler import Query
import sys
import os
from base64 import b64encode

from pprint import pprint
import requests
import xmltodict
from urllib.parse import urlparse, urlunparse
from urllib.request import url2pathname


# Non standard modules (install with pip)

ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../common"))


# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(ScriptPath))
# own local modules
from classes import MovieInfo
import defaults
from splthread import SplThread
from jsonstorage import JsonStorage
from streamchannels import StreamChannel
from scheduler import Scheduler

# requests local file:// adaptor https://stackoverflow.com/a/27786580
class LocalFileAdapter(requests.adapters.BaseAdapter):
	"""Protocol Adapter to allow Requests to GET file:// URLs

	@todo: Properly handle non-empty hostname portions.
	"""

	@staticmethod
	def _chkpath(method, path):
		"""Return an HTTP status for the given filesystem path."""
		if method.lower() in ('put', 'delete'):
			return 501, "Not Implemented"  # TODO
		elif method.lower() not in ('get', 'head'):
			return 405, "Method Not Allowed"
		elif os.path.isdir(path):
			return 400, "Path Not A File"
		elif not os.path.isfile(path):
			return 404, "File Not Found"
		elif not os.access(path, os.R_OK):
			return 403, "Access Denied"
		else:
			return 200, "OK"

	def send(self, req, **kwargs):  # pylint: disable=unused-argument
		"""Return the file specified by the given request

		@type req: C{PreparedRequest}
		@todo: Should I bother filling `response.headers` and processing
				   If-Modified-Since and friends using `os.stat`?
		"""
		path = os.path.normcase(os.path.normpath(url2pathname(req.path_url)))
		response = requests.Response()

		response.status_code, response.reason = self._chkpath(req.method, path)
		if response.status_code == 200 and req.method.lower() != 'head':
			try:
				response.raw = open(path, 'rb')
			except (OSError, IOError) as err:
				response.status_code = 500
				response.reason = str(err)

		if isinstance(req.url, bytes):
			response.url = req.url.decode('utf-8')
		else:
			response.url = req.url

		response.request = req
		response.connection = self

		return response

	def close(self):
		pass


class SplPlugin(StreamChannel):
	plugin_id = 'channels_satip'
	plugin_names = ['SatIP Live']

	def __init__(self, modref):
		''' inits the plugin
		'''
		# do the plugin specific initialisation first
		self.origin_dir = os.path.dirname(__file__)
		self.config = JsonStorage(self.plugin_id, 'backup', "config.json", {
			'channel_list_urls': [
				{
					'url': 'file:///Astra_19.2.xspf',
					'type':'xspf',
					'scheme': 'http',
					'netloc': '192.168.1.131'
				},
				{
					'url': 'file:///ASTRA_19_2E.m3u',
					'type':'m3u',
					'scheme': '',
					'netloc': ''
				},
			]
		}
		)

		# at last announce the own plugin
		super().__init__(modref)
		modref.message_handler.add_event_handler(
			self.plugin_id, 0, self.event_listener)
		modref.message_handler.add_query_handler(
			self.plugin_id, 0, self.query_handler)

	def add_movie(self, provider, full_url):
		plugin_name = self.plugin_names[0]
		source_type = defaults.MOVIE_TYPE_STREAM
		self.providers.add(provider)
		new_movie = MovieInfo(
			url=full_url,
			mime='video/MP2T',
			title=provider+' Live',
			category='live',
			source=plugin_name,
			source_type=source_type,
			provider=provider,
			timestamp=0,
			duration=0,
			description='',
			# we have to handmade the uri here to not have the title crc32 hash as part of it
			uri=':'.join([plugin_name, provider, '0'])
		)

		if not plugin_name in self.movies:
			self.movies[plugin_name] = {}
		self.movies[plugin_name][new_movie['uri']] = new_movie

	def load_xspf(self, req,scheme,netloc):
		try:
			root = xmltodict.parse(req.text)
			for track in root['playlist']['trackList']['track']:
				provider = track['title']
				#print (track['album'])
				location = track['location']
				url_st = urlparse(location)
				if scheme:
					this_scheme= scheme
				else:
					this_scheme= url_st.scheme
				if netloc:
					this_netloc=netloc
				else:
					this_netloc=url_st.netloc
				full_url = urlunparse((
					this_scheme,
					this_netloc,
					url_st.path,
					url_st.params,
					url_st.query,
					url_st.fragment,
				))
				# print(full_url)
				self.add_movie(provider, full_url)
		except Exception as e:
			print(str(e))

	def load_m3u(self, req,scheme,netloc):
		try:
			is_provider_line=False
			for line in req.iter_lines(decode_unicode=True):
				line = line.decode('utf-8').strip()
				try:
					if line.upper().startswith('#EXTINF:'):
						provider = line.split(',',maxsplit=1)[1]
						is_provider_line=True
					else:
						if not is_provider_line:
							continue
						if line:  # if not eol
							is_provider_line=False
							url_st = urlparse(line)
							if scheme:
								this_scheme= scheme
							else:
								this_scheme= url_st.scheme
							if netloc:
								this_netloc=netloc
							else:
								this_netloc=url_st.netloc
							full_url = urlunparse((
								this_scheme,
								this_netloc,
								url_st.path,
								url_st.params,
								url_st.query,
								url_st.fragment,
							))
							# print(full_url)
							self.add_movie(provider, full_url)
				except Exception as e:
					print('mailformed m3u element {0}'.format(str(e)))

		except Exception as e:
			print(str(e))

	def loadChannels(self):
		for channel_info in self.config.read('channel_list_urls'):
			requests_session = requests.session()
			url_st = urlparse(channel_info['url'])
			path= url_st.path
			if url_st.scheme=='file':
				path=os.path.normcase(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),path[1:])))
			full_url = urlunparse((
				url_st.scheme,
				url_st.netloc,
				path,
				url_st.params,
				url_st.query,
				url_st.fragment,
			))

			requests_session.mount('file://', LocalFileAdapter())
			req = requests_session.get(full_url)

			if channel_info['type'] == 'xspf':
				self.load_xspf(req,channel_info['scheme'],channel_info['netloc'])
			if channel_info['type'] == 'm3u':
				self.load_m3u(req,channel_info['scheme'],channel_info['netloc'])
