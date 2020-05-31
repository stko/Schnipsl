#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from webserver import Webserver
from simulator import Simulator
from messagehandler import MessageHandler
import storage
import schnipsllogger

class ModRef:
	''' helper class to store references to the global modules
	'''
	
	def __init__(self):
		self.server = None
		self.store = None
		self.message_handler = None


def _(s): return s

logger = schnipsllogger.getLogger(__name__)


modref = ModRef() # create object to store all module instances
modref.store = storage.Storage(modref)
modref.message_handler = MessageHandler(modref)
modref.server = Webserver(modref)
si=Simulator(modref)
si.run()
modref.server.run()

while(True):
	time.sleep(1)
