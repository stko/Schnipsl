#!/usr/bin/env python
# -*- coding: utf-8 -*-

from HTTPWebSocketsHandler import HTTPWebSocketsHandler
'''
credits:
combined http(s) and websocket server copied from
	https://github.com/PyOCL/httpwebsockethandler
	The MIT License (MIT)
	Copyright (c) 2015 Seven Watt

'''


import sys
import os
import queue
import copy
from threading import Thread, Lock

import defaults


class EventListener:
	''' stores event listener specific data
	'''

	def __init__(self, name, priority, event_handler):
		self.name = name
		self.priority = priority
		self.event_handler = event_handler

class QueryHandler:
	''' stores query handler  specific data
	'''

	def __init__(self, name, priority, query_handler):
		self.name = name
		self.priority = priority
		self.query_handler = query_handler


class QueueEvent:
	''' stores event  specific data
	'''

	def __init__(self, user, ev_type, data):
		self.user = user
		self.type = ev_type
		self.data = data

class Query:
	''' stores query  specific data
	'''

	def __init__(self, user, qu_type, params):
		self.user = user
		self.type = qu_type
		self.params = params


class MessageHandler:
	'''does the event- based message handling
	'''

	def __init__(self, modref):
		self.event_listeners = []
		self.query_handlers = []
		self.modref = modref
		self.queue = queue.Queue()  # data queue
		self.mutex = Lock()  # prepare lock for atomar data changes
		self.th = Thread(target=self.run)
		# Start the thread
		self.th.setDaemon(True)
		self.th.start()

	def run(self):
		''' endless thread loop to distribute all incoming events to all eventlistener
		'''

		print("message handler thread loop")
		while True:
			queue_event = self.queue.get(
				block=True)  # waits for incoming queue_event objects
			for event_handler in self.event_listeners:
				# allows the handler to modify the event (just for later extensions :-)
				queue_event = event_handler.event_handler(queue_event)
				if not queue_event:  # if eventhandler returns Null, then no further message handling
					break


	def add_event_handler(self, name, priority, event_handler):

		self.mutex.acquire()  # avoid thread interfearence
		self.event_listeners.append(
			EventListener(name, priority, event_handler))
		# release the mutex lock
		self.mutex.release()

	def add_query_handler(self, name, priority, query_handler):

		self.mutex.acquire()  # avoid thread interfearence
		self.query_handlers.append(
			QueryHandler(name, priority, query_handler))
		# release the mutex lock
		self.mutex.release()

	def queue_event(self, owner, ev_type, data):
		self.queue.put(QueueEvent(owner, ev_type, data))

	def queue_event_obj(self, queue_event):
		self.queue.put(queue_event)

	def query(self, query):
		res=[]
		for query_handler in self.query_handlers:
			if defaults.MAX_QUERY_SIZE-len(res)<=0:
				break
			res += query_handler.query_handler(query,defaults.MAX_QUERY_SIZE-len(res))
		return res
