#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard module
import sys
import os
import time
import datetime
import lzma
import time
from urllib.request import urlopen,urlretrieve,  urlparse, urlunparse
from xml.etree.ElementTree import parse

try:
	file_name=sys.argv[1]
	with open(file_name+'_unpack_test','wb') as unpack_file_handle:
		unpack_file_handle.write(lzma.open(file_name).read())
		print('filmlist server list unpacked')
except  Exception as e:
	print('failed filmlist unpack',str(e))
