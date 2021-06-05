#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import schnipsllogger

logger = schnipsllogger.getLogger(__name__)

class DirectoryMapper:
	'''in some environments like docker it is essential to map directories to some other locations

	This DirectoryMapper creates class specific subdirectories in predefined parent folders,
	where then each class can store it's own files without taking care about the real location

	'''

	path_settings={}

	@classmethod
	def __init__(cls, root_path,initial_path_settings):
		if cls.path_settings:
			logger.error('multiple initialization: pathsettings already initialized!')
		cls.path_settings=initial_path_settings
		cls.root_path=root_path

	@classmethod
	def open(cls, module_name,storage_type,file_name, rw_type='r'):
		'''
		identifies the absolut path of the requested storage_type,
		creates a owner class specific subfolder and returns the file handle

		Args:
			owner (:obj:`obj`) : instance the file belongs to
			storage_type (:str:`str`): identifier of the wanted storage type
			file_name (:str:`str`):file name without! path

		'''
		if not cls.path_settings:
			logger.error('DirectoryMapper not initialized!')
			raise IOError
		if not storage_type in cls.path_settings:
			logger.error(f'unknown storage type {storage_type}')
			raise IOError
		owner_dir=os.path.abspath(os.path.join(cls.root_path,cls.path_settings[storage_type],module_name))
		if not os.path.exists(owner_dir):
			os.makedirs(owner_dir)
		full_file_name=os.path.join(owner_dir,file_name)
		return  open(full_file_name,rw_type) 


