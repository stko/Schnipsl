#!/usr/bin/env python
# -*- coding: utf-8 -*-

from splthread import SplThread
from messagehandler import Query
from classes import MovieInfo
import defaults
from defaults import Record_States
from scheduler import Scheduler
from jsonstorage import JsonStorage
import json
import os
import sys
import time
import threading
import base64
import subprocess

from urllib.parse import urlparse

# Standard module


# Non standard modules (install with pip)


# own local modules
ScriptPath = os.path.realpath(os.path.join(
	os.path.dirname(__file__), "../../../common"))


# Add the directory containing your module to the Python path (wants absolute paths)
sys.path.append(os.path.abspath(ScriptPath))

import schnipsllogger

logger = schnipsllogger.getLogger(__name__)

class SplPlugin(SplThread):
	plugin_id = 'record_hd'
	plugin_names = ['HD Recorder']

	def __init__(self, modref):
		''' inits the plugin
		'''
		self.modref = modref

		# do the plugin specific initialisation first
		self.origin_dir = os.path.dirname(__file__)
		self.config = JsonStorage(self.plugin_id, 'backup', "config.json", {'path': '/var/schnipsl', 'www-root': 'http://schnipsl:9092/'})
		self.records = JsonStorage(self.plugin_id, 'runtime', "records.json", {})
		self.record_threats={} # we need to store the thread pointers seperate from self.records, as we can't store them as json
		self.last_recorded_time =  0 # remembers how long the last recording action is away

		# at last announce the own plugin
		super().__init__(modref.message_handler, self)
		modref.message_handler.add_event_handler(
			self.plugin_id, 0, self.event_listener)
		modref.message_handler.add_query_handler(
			self.plugin_id, 0, self.query_handler)
		self.runFlag = True

	def event_listener(self, queue_event):
		if queue_event.type == defaults.TIMER_RECORD_REQUEST:
			self.timer_record_request(queue_event.data)
		# for further pocessing, do not forget to return the queue event
		return queue_event

	def query_handler(self, queue_event, max_result_count):
		''' try to send simulated answers
		'''
		# logger.info(f"hd_recorder query handler" {queue_event.type}  {queue_event.user} {max_result_count"})
		if queue_event.type == defaults.QUERY_MOVIE_ID:
			new_uri=queue_event.params
			for record_movie in self.records.read('all',{}).values(): # 'all': read the whole config
				if record_movie['new_uri']==new_uri:
					return [MovieInfo(
								source=self.plugin_names[0],
								source_type=defaults.MOVIE_TYPE_RECORD,
								provider=record_movie['new_uri'].split(':')[1], # extracts the original provider back out of the uri
								category=record_movie['category'],
								title=record_movie['title'],
								timestamp=record_movie['timestamp'],
								duration=record_movie['duration'],
								description=record_movie['description'],
								url=record_movie['new_url'],
								mime=record_movie['mime']

					)]

		return[]

	def _run(self):
		''' starts the server
		'''
		scheduler = Scheduler(
			[(self.check_for_records, 10), (self.cleanup_records, 60)])
		while self.runFlag:
			scheduler.execute()
			time.sleep(2)

	def _stop(self):
		self.runFlag = False

	def timer_record_request(self, data):
		uri = data['uri']
		uuid = data['uuid']
		movie_info_list = self.modref.message_handler.query(
			Query(None, defaults.QUERY_MOVIE_ID, uri))
		if movie_info_list:
			movie_info = movie_info_list[0]
			uri = movie_info['uri']
			# do we have that record request already
			existing_record = self.records.read(uri)
			if not existing_record:
				uri_base64 = base64_encode(uri)
				ext='.mp4'
				if movie_info['mime']=='video/MP2T':
					ext='.mp4'
				file_path = os.path.join(
					self.config.read('path'), uri_base64+ext)
				if movie_info['source_type'] == defaults.MOVIE_TYPE_RECORD:
					self.records.write(uri, {
						# in case of a record we set start and duration to 0 to indicate that the recording can start immediadly & has no duration
						'record_starttime': 0,
						'record_duration': 0,
						'provider': movie_info['provider'],
						'category': movie_info['category'],
						'title': movie_info['title'],
						'timestamp': movie_info['timestamp'],
						'duration': movie_info['duration'],
						'description': movie_info['description'],
						'url': movie_info['url'],

						'uri': uri,
						'new_uri': self.plugin_names[0]+':'+':'.join(movie_info['uri'].split(':')[1:]),
						'new_url': self.config.read('www-root')+uri_base64+ext,
						'uuid': uuid,
						'file_path': file_path,
						'state': Record_States.WAIT_FOR_RECORDING,
						'errorcount': 4 # try to start the record up to 4 times before it finally failes
					})
				if movie_info['source_type'] == defaults.MOVIE_TYPE_STREAM:
					# recording a stream with a duration of 0 is a very bad idea, because it would never stop..
					if movie_info['duration']:
						self.records.write(uri, {
							'record_starttime': movie_info['timestamp'],
							'record_duration': movie_info['duration'],
							'category': movie_info['category'],
							'title': movie_info['title'],
							'timestamp': movie_info['timestamp'],
							'duration': movie_info['duration'],
							'description': movie_info['description'],
							'url': movie_info['url'],
							'mime': movie_info['mime'],
							'uri': uri,
							'new_uri': self.plugin_names[0]+':'+':'.join(movie_info['uri'].split(':')[1:]),
							'new_url': self.config.read('www-root')+uri_base64+ext,
							'uuid': uuid,
							'file_path': file_path,
							'state': Record_States.WAIT_FOR_RECORDING,
							'errorcount': 4 # try to start the record up to 4 times before it finally failes
						})
	
	def check_for_records(self):
		act_time = time.time()
		for uri, record in self.records.read('all','').items():
			if record['state'] == Record_States.WAIT_FOR_RECORDING:
				if record['record_duration'] == 0:  # this is a record, which can be recorded immediadly
					record['state'] = Record_States.ACTUAL_RECORDING
					self.records.write(uri, record)
					self.recording(record)
					continue
				# something went wrong, the record time was in the past. Mark the entry as failed
				if record['record_starttime']+record['record_duration'] < act_time:
					record['state'] = Record_States.RECORDING_FAILED
				# something went wrong during recording
				if record['state'] == Record_States.RECORDING_FAILED:
					self.records.write(uri, record)
					self.deploy_record_result(record, record['state'])
					continue
				# it's time to start
				if record['record_starttime']-self.config.read('padding_secs', 300) <= act_time and record['record_starttime']+record['record_duration'] > act_time:
					# in case the movie has already started, we correct starttime and duration to show the real values
					if record['record_starttime'] < act_time:
						record['starttime'] = str(act_time)
						record['duration'] = record['duration'] - (act_time - record['record_starttime'])
					record['state'] = Record_States.ACTUAL_RECORDING
					self.records.write(uri, record)
					self.recording(record)
					continue

	def cleanup_records(self):
		records_to_delete={}
		act_time=time.time()
		# request which movies are still in the UI list
		valid_movieuri_list = self.modref.message_handler.query(
				Query(None, defaults.QUERY_VALID_MOVIE_RECORDS, {'source':self.plugin_names[0]}))
		for uri, record in self.records.config.items():
			if uri in self.record_threats:
				# recording is finished, so deploy the result
				if not self.record_threats[uri].is_alive():
					del(self.record_threats[uri])  # we destroy the thread
					self.deploy_record_result(record,
						record['state'] )
					self.last_recorded_time=act_time
			if self.last_recorded_time> act_time-5*60:
				return # don't do any delete action if the last record is just 5 mins ago to give the UI some time to adapt the new movie
			if record['state'] == Record_States.ACTUAL_RECORDING and not uri in self.record_threats: # seems to be a zombie record
				records_to_delete[uri]=record
				self.deploy_record_result(record,
						Record_States.RECORDING_FAILED )
			if record['state'] == Record_States.RECORDING_FINISHED or record['state'] == Record_States.RECORDING_FAILED:
				new_uri=record['new_uri']
				#logger.info(f'Record on disk: {new_uri}') 
				if not new_uri in valid_movieuri_list:
					records_to_delete[uri]=record
		# some debug output
		#for uri in valid_movieuri_list:
		#	logger.info(f'recoder uri: {uri}')
		if records_to_delete:
			# go through the list of records to be deleted
			for uri,  record in records_to_delete.items():
				# delete the file
				file_path=record['file_path']
				logger.info(f'try to delete file {file_path}' )
				if os.path.exists(file_path):
					try:
						os.remove(file_path)
						logger.info(f'file deleted {file_path}' )
					except Exception as ex:
						logger.warning("Cant delete record file {0}. Error: {1}".format(file_path,str(ex)))
				else:
					# remove the entry
					logger.info(f'file not found, just remove the entry {uri}' )
				del(self.records.config[uri])
			self.records.save()

	def deploy_record_result(self, record, record_state):
		# save changes
		self.records.write(record['uri'], record)
		self.modref.message_handler.queue_event(None, defaults.TIMER_RECORD_RESULT, {
			'new_uri':record['new_uri'], 'new_url':record['new_url'], 'uuid': record['uuid'], 'record_state': record_state})

	def recording(self, record):
		uri=record['uri']
		logger.info(f'try to record {uri}')
		threat = threading.Thread(target=record_thread, args=(
			record, self.config.read('padding_secs', 300)))
		self.record_threats[uri] = threat
		threat.start()


def record_thread(record, padding_time):
	file_path = record['file_path']
	url = record['url']
	act_time = time.time()
	remaining_time = record['record_starttime']+record['record_duration']-act_time

	################ debug tweak to keep the records short - reduce the records to 30 secs.
	if False:
		remaining_time=25
		padding_time=5

	attr = None
	# does the record has a duration? then we've use ffmeg to limit the duration
	if record['record_duration']:
		# attr = ['ffmpeg', '-y', '-i', url, '-vcodec', 'copy', '-acodec', 'copy', 	'-map', '0:v', '-map', '0:a', '-t', str(remaining_time+padding_time), '-f', 'ts' , file_path]
		attr = ['ffmpeg', '-y', '-rw_timeout', '5000',  '-i', url, '-vcodec', 'copy', '-acodec', 'copy', '-t', str(remaining_time+padding_time), file_path]
	else:
		attr = ['curl', '-s', url, '-o', file_path]  # process arguments
	if attr:
		logger.info(f"recorder started {repr(attr)}" )
		try:
			completed_process = subprocess.run(attr)
			if completed_process.returncode:
				logger.warning("recorder ended with an error:\n%s" %
					  (completed_process.returncode))
				try:
					record['errorcount']-=1
				except:
					record['errorcount']=4 # just a temporary fix to avoid a crash on older configs
				if record['errorcount']<=0:
					record['state'] = Record_States.RECORDING_FAILED
					logger.info(f"recorder max error count reached, recording finally failed" )
				else: # give it another try
					record['state'] =Record_States.WAIT_FOR_RECORDING
					logger.info(f"recorder error count {record['errorcount']}, try it again soon.." )
			else:
				logger.info("recorder ended")
				record['state'] = Record_States.RECORDING_FINISHED
		except Exception as ex:
			logger.warning("recorder could not be started. Error: %s" % (ex))
	else:
		record['state'] = Record_States.RECORDING_FAILED


def base64_encode(string):
	"""
	Removes any `=` used as padding from the encoded string.
	"""
	encoded = base64.urlsafe_b64encode(string.encode())
	return encoded.decode().replace('=', '')

def base64_decode(string):
	"""
	Adds back in the required padding before decoding.
	"""
	padding = 4 - (len(string) % 4)
	string = string + ("=" * padding)
	return base64.urlsafe_b64decode(string).decode()
