#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import os
import threading
from abc import ABCMeta, abstractmethod


class SplThread(metaclass=ABCMeta):
	'''Partly abstract class to implement threading & message handling
	'''

	def __init__(self, msg_handler, child):
		self.msg_handler = msg_handler
		self.child = child

	@abstractmethod
	def _run(self):
		''' starts the thread loop
		'''
		pass

	@abstractmethod
	def _stop(self):
		''' stops the thread loop
		'''
		pass

	def run(self):
		''' starts the child thread
		'''
		# Create a Thread with a function without any arguments
		#th = threading.Thread(target=_ws_main, args=(server,))
		self.th = threading.Thread(target=self.child._run)
		# Start the thread
		self.th.setDaemon(True)
		self.th.start()

	def stop(self, timeout=0):
		''' stops the child thread. If timeout > 0, it will wait timeout secs for the thread to finish
		'''
		self.child._stop()
		if timeout > 0:
			self.th.join(timeout)
		return self.th.isAlive()
