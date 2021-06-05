#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard module
import sys
import os
import json
from base64 import b64encode
from threading import Timer , Lock
import time
import datetime
import calendar
import subprocess
import time
from urllib.request import urlopen, urlretrieve,  urlparse, urlunparse
from xml.etree.ElementTree import parse
import re

# Non standard modules (install with pip)
from whoosh.qparser import QueryParser


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
import defaults
from epgprovider import EPGProvider
import schnipsllogger

class SplPlugin(EPGProvider):
	plugin_id = 'satepg'
	plugin_names = ['SAT EPG']

	def __init__(self, modref):
		''' inits the plugin
		'''
		self.modref = modref
		self.logger = schnipsllogger.getLogger(__name__)

		# do the plugin specific initialisation first
		self.origin_dir = os.path.dirname(__file__)
		self.config = JsonStorage(self.plugin_id, 'backup' ,"config.json", {
				'epgloops':1,
				'epgtimeout':60,
				'stream_source':'SatIP Live'
			}
		)
		self.stream_source=self.config.read('stream_source') # this defines who is the real data provider for the entries found in the EPG data

		self.epgbuffer_file_name = os.path.join(self.origin_dir, "epgbuffer.ts")

		self.process=None
		self.epg_storage = JsonStorage(self.plugin_id, 'runtime',  "epgdata.json", {'epgdata':{}})
		self.all_EPG_Data = self.epg_storage.read('epgdata')


		self.timeline = {}

		# at last announce the own plugin
		super().__init__(modref, self.origin_dir)
		modref.message_handler.add_event_handler(
			self.plugin_id, 0, self.event_listener)
		modref.message_handler.add_query_handler(
			self.plugin_id, 0, self.query_handler)


		# plugin specific stuff
		# each EPG has its own special hardwired categories

		self.categories = [
			{
				'text': 'category_today',
				'value': '{"type": "day", "expression": "today"}'
			},
			{
				'text': 'category_tomorrow',
				'value': '{"type": "day", "expression": "tomorrow"}'
			},
			{
				'text': 'category_now',
				'value': '{"type": "time", "expression": "now"}'
			},
			{
				'text': 'category_evening',
				'value': '{"type": "time", "expression": "[\'8 PM\' to tomorrow"}'
			},
		]



	def event_listener(self, queue_event):
		''' react on events
		'''
		#print("event handler", self.plugin_id, queue_event.type, queue_event.user)
		if queue_event.type == defaults.STREAM_REQUEST_PLAY_LIST:
			self.stream_answer_play_list(queue_event)
		return queue_event  # dont forget the  event for further pocessing...

	def get_real_plugin_name(self,initial_plugin_name):
		''' helper routine, as on some epg types we need to correct the plugin name
		if this is the case, this method need to return its corrected plugin name
		'''
		return self.stream_source

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
		return False


	# ------ plugin specific routines

	def getAbsolutePath(self, file_name):
		return os.path.join(self.origin_dir, file_name)

	def check_for_updates(self):
		# check for updates:
		# we'll use the name of the stream source plugin instead the name of the EPG plugin itself
		plugin_name = self.stream_source
		new_epg_loaded=False
		actual_time=time.time()
		with self.whoosh_ix.writer() as whoosh_writer:
			# we need to make a local copy first  of the providers to avoid a "array changed size during iteration" error
			for provider in list(self.all_EPG_Data.keys()):
				if self.all_EPG_Data[provider]['requested']:
					self.all_EPG_Data[provider]['requested']=False
					if self.all_EPG_Data[provider]['lastmodified']<actual_time-60*60 or not self.all_EPG_Data[provider]['epg_data']:
						time.sleep(10) # give the sat receiver some time to recover?!?!?!
						epg_details = self.get_epg_from_receiver(
							provider,self.all_EPG_Data[provider]['url'])
						if epg_details:
							new_epg_loaded=True
							self.all_EPG_Data[provider]['lastmodified'] = time.time()
							for start_time, movie_info in epg_details.items():
								# refresh or add data
								if int(start_time)< actual_time+ 24*60*60: # only if the movie starts within the next 24 h, store it in Memory
									self.all_EPG_Data[provider]['epg_data'][start_time] = movie_info
								# fill the search engine
								whoosh_writer.update_document(
									source=plugin_name,
									source_type=defaults.MOVIE_TYPE_STREAM,
									provider=provider,
									title=movie_info['title'],
									category=movie_info['category'],
									uri=movie_info['uri'],
									url=movie_info['url'],
									mime=movie_info['mime'],
									duration=movie_info['duration'],
									description=movie_info['description'],
									timestamp=datetime.datetime.fromtimestamp(int(movie_info['timestamp']))
								)
							# do to only one epg update at a time and give the other threads some recources, we'll
							# stop the loop after each providerupdate and wait for the next one
							break


					movie_infos_to_delete={}
					max_age_timestamp=actual_time - 6* 60*60 # the movie started at least six hour ago
					max_age_timestamp_datetime=datetime.datetime.fromtimestamp(max_age_timestamp)
					for start_time, movie_info in self.all_EPG_Data[provider]['epg_data'].items():
						if int(start_time) <max_age_timestamp:
							movie_infos_to_delete[start_time]=movie_info['uri']
					for start_time,uri in movie_infos_to_delete.items():
						del(self.all_EPG_Data[provider]['epg_data'][start_time])
						new_epg_loaded=True
					if movie_infos_to_delete:
						qp = QueryParser('timestamp', schema=self.whoosh_ix.schema)
						querystring = "timestamp:[19700101 to {0}]".format(max_age_timestamp_datetime.strftime('%Y%m%d%H%M%S'))
						q = qp.parse(querystring)
						whoosh_writer.delete_by_query(q)
			#delete old provider
			for provider_reference in list(self.all_EPG_Data.keys()):
				if self.all_EPG_Data[provider_reference]['lastmodified']<actual_time-24*60*60: # no update the last 24 h? remove it..
					whoosh_writer.delete_by_term('provider',provider_reference)
					del(self.all_EPG_Data[provider_reference])
					new_epg_loaded=True
		if self.providers and not new_epg_loaded: # if this is not the first call (self.provides contains already data),but no new epg data
			return
		self.epg_storage.write('epgdata',self.all_EPG_Data)

		# refill the internal lists
		new_providers = set()
		new_timeline = {}
		# EPG has its own special hardwired categories
		#self.categories = set()
		if not plugin_name in self.movies: 
			self.movies[plugin_name] = {}
		for provider, movie_data in self.all_EPG_Data.copy().items():
			new_providers.add(provider)
			new_timeline[provider] = []
			for movie_info in movie_data['epg_data'].values():
				new_timeline[provider].append(type('', (object,), {
												'timestamp': movie_info['timestamp'], 'movie_info': movie_info})())
				self.movies[plugin_name][movie_info['uri']] = movie_info
		#replace the old data with the new one
		self.providers = new_providers
		self.timeline = new_timeline
		# sort by datetime
		for epg_list in self.timeline.values():
			epg_list.sort(key=self.get_timestamp)


	def search_channel_info(self, channel_epg_name):
		channels_info = self.channels_info.read('channels_info')
		if channels_info:
			for channel_info in channels_info:
				if channel_info['channel_epg_name'] == channel_epg_name:
					return channel_info

	def split_text_by_capital_chars(self,text):
		'''
		Tricky: Somehow the text in EPG seems not to have a line seperator ?!?, but it helps to 
		split the text wherever a capital letter follows a small letter or digit like in 
		
		erster SatzZweiter Satz2009Dritter Satz

		which gives
		erster Satz
		Zweiter Satz2009
		Dritter Satz
		'''
		pattern = re.compile(r'([^\sA-Z])([A-Z])')
		# step 1: insert a seperator in between
		newstring = pattern.sub(r"\1\n\2", text)
		# step 2: split by that seperator
		return newstring.split('\n')

	def get_epg_from_receiver(self, provider,url):
		# reduce the pids to the ones containing SDT (0x11) and EIT (0x12)
		url_st = urlparse(url)
		queries = url_st.query
		new_queries = ""
		if queries:
			for eq in queries.split("&"):
				key = eq.split("=")[0]
				value = eq.split("=")[1]
				if key == 'pids':
					value = "0,17,18"
				new_queries += key + "=" + value + "&"
		new_queries = new_queries.strip("&")
		url_epd_pids_only = urlunparse((
			url_st.scheme,
			url_st.netloc,
			url_st.path,
			url_st.params,
			new_queries,
			url_st.fragment,
		))



		attr=[os.path.join(	self.origin_dir, 'epg_grap.sh') , url_epd_pids_only, provider , str(self.config.read('epgloops')), str(self.config.read('epgtimeout'))] # process arguments
		self.logger.info  ("epg_grap started {0} {1} {2}".format(provider, url_epd_pids_only,repr(attr)))
		try:
			self.process = subprocess.Popen(attr, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			cleaner = Timer(600, self.cleanProcess) # if epg_grap won't exit, try to terminate its process in 30 seconds
			cleaner.start()
			epg_out, err = self.process.communicate()
			#self.process.wait() # oops... not needed? harmless!
			cleaner.cancel()
			if err:
				self.logger.warning ("epg_grap ended with an error:\n%s" % ( err))
			else:
				self.logger.debug ("epg_grap' ended")
				epg_json_string=epg_out.decode()
				epg_json = json.loads(epg_json_string)
				result = {}
				count = 0
				for json_movie in epg_json['details'].values():
					start = json_movie['unixTimeBegin']
					stop = json_movie['unixTimeEnd']
					if json_movie['title']:
						title = self.split_text_by_capital_chars(json_movie['title'])[0]
					else:
						title = json_movie['name']
					desc = '\n'.join(self.split_text_by_capital_chars(json_movie['description']))
					category =  json_movie['name']
					count += 1

					# we'll use the name of the stream source plugin instead the name of the EPG plugin itself
					# plugin_name = self.plugin_names[0]
					plugin_name = self.stream_source
					self.providers.add(provider)
					# EPG has its own special hardwired categories
					#self.categories.add(category)
					new_movie = MovieInfo(
						url = url,
						mime = 'video/MP2T',
						title = title,
						category = category,
						source = plugin_name,
						source_type = defaults.MOVIE_TYPE_STREAM,
						provider = provider,
						timestamp = int(start),
						duration = stop-start,
						description = desc
					)

					if not plugin_name in self.movies:
						self.movies[plugin_name]={}
					self.movies[plugin_name][new_movie['uri']]=new_movie
					result[start]=new_movie
				for json_provider in epg_json['providers']:
					self.logger.debug("channel found in epg: {0}".format(json_provider))
				self.logger.info("{0} epg loaded, {1} entries".format(provider,count))
				return result
		except Exception as ex:
			self.logger.warning ("epg_grap could not be started. Error: %s" % (ex))
		return

	def get_timestamp(self, elem):
		'''helper function for the array sort function
		'''
		return elem.timestamp

	def string_to_timestamp(self, timestring):
		if timestring:
			# read https://stackoverflow.com/a/2956997 to understand why timegm() is used insted of mktime()!
			return calendar.timegm(datetime.datetime.strptime(timestring, "%Y%m%d%H%M%S %z").timetuple())
		else:
			return ''

	def stream_answer_play_list(self,queue_event):
		uri= queue_event.data['uri']
		uri_elements =uri.split(':')
		source=uri_elements[0]
		if source != self.stream_source:
			return queue_event
		provider = uri_elements[1]
		if not provider in self.all_EPG_Data:
			movie_info_list = self.modref.message_handler.query(
				Query(None, defaults.QUERY_MOVIE_ID, source+':'+provider+':0'))
			if movie_info_list:
				movie_info= movie_info_list[0]
				with self.lock:
					self.all_EPG_Data[provider]={
						'requested':True,
						'url':movie_info['url'],
						'epg_data' : {},
						'lastmodified' : 0
					}
		else:
			self.all_EPG_Data[provider]['requested']=True
		time_stamp = time.time()
		try:
			epg_list =[]
			if provider in self.timeline:
				epg_list = self.timeline[provider]
			nr_of_entries = len(epg_list)
			i = 0
			while i < nr_of_entries and time_stamp > int(epg_list[i].timestamp):
				i += 1
			if i < nr_of_entries and i>0 and time_stamp <  int(epg_list[i-1].timestamp)+int(epg_list[i-1].movie_info['duration']):  # we found an entry
				first_movie_info=epg_list[i-1].movie_info
				second_movie_info=epg_list[i].movie_info
				processed_time_percentage=(time_stamp-int(first_movie_info['timestamp']))*100/first_movie_info['duration']
				if processed_time_percentage<0:
					processed_time_percentage=0
				if processed_time_percentage>100:
					processed_time_percentage=100
				combined_movie_info=MovieInfo(
					url=first_movie_info['url'],
					mime=first_movie_info['mime'],
					source=first_movie_info['source'],
					source_type =first_movie_info['source_type'],
					uri=first_movie_info['uri'],
					title=first_movie_info['title'],
					category=first_movie_info['category'],
					next_title=second_movie_info['title'],
					provider=first_movie_info['provider'],
					timestamp=second_movie_info['timestamp'],
					duration=processed_time_percentage,  # 
					description=first_movie_info['description'],
					query=first_movie_info['query']
				)
				combined_movie_info['recordable']=True
			else:
				combined_movie_info=MovieInfo(
					url='',
					mime='',
					source='',
					source_type ='',
					uri=':'.join([self.stream_source,provider,'0']),
					title='-',
					category='',
					provider=provider,
					timestamp=time_stamp,
					duration=0,  # 
					description='',
					query=None
				)
				combined_movie_info['recordable']=False
				# as we didn't found a matching EPG record, we "rewind" the provider update time by 2 hours to force another epg read
				self.all_EPG_Data[provider]['lastmodified']=time.time()-2*60*60




			self.modref.message_handler.queue_event(None, defaults.STREAM_ANSWER_PLAY_LIST, {'uri': queue_event.data['uri'],'movie_info':combined_movie_info})
		except Exception as e:
			print('unknown provider', provider, str(e))

	def cleanProcess(self):
		try:
			if not self.process==None:
				self.process.terminate()
			time.sleep(3)
			if not self.process==None:
				self.process.kill()
				print ("Curl had to be killed. R.I.P.")
			else:
				print ("Curl had to be terminated.")
		except:
			print ("Curl termination error, process might be running")
		if not self.process==None:
			print ("Curl: termination may have failed")
		self.running = 0
