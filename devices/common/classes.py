#!/usr/bin/env python
# -*- coding: utf-8 -*-

import defaults

class MovieInfo(dict):
	'''helper class to store the movie clips information to sent to the client
	'''

	def __init__(self, url, mime, title, category, source, source_type, provider, timestamp, duration, description,query=None,next_title=None, uri=None):
		if not uri:
			self['uri'] = ':'.join([source,provider,str(timestamp),str(hash(title))]) # we use the hash of the title as ARD Mediathek has the same movie at the same time, but with different languages
		else:
			self['uri']=uri
		self['url'] = url
		self['mime'] = mime
		self['query'] = query
		self['title'] = title
		self['category'] = category		
		self['next_title'] = next_title		# for live stream infos this will be used as the title of the 2. movie
		self['source'] = source
		self['source_type'] = source_type
		self['provider'] = provider
		self['timestamp'] = timestamp	# for live stream infos this will be used as the start time of the 2. movie
		self['duration'] = duration 	# for live stream infos this will be used as already played time of the 1. movie in percent
		self['description'] = description
		self['streamable'] = False # e.g. EPG items can not be streamed, only recorded
		self['recordable'] = False # live streams can not be recorded, as they don't have a duration, they are endless
		if source_type == defaults.MOVIE_TYPE_STREAM:
			self['recordable'] = True

