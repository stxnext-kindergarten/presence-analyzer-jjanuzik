# -*- coding: utf-8 -*-
"""
This module updates users.xml file
"""

import urllib2

from presence_analyzer.main import app

with open(app.config['DATA_XML'], 'w') as xmlfile:
    RESPONSE = urllib2.urlopen('http://sargo.bolt.stxnext.pl/users.xml')
    xmlfile.turncate()
    NEW_DATA = RESPONSE.read()
    xmlfile.write(NEW_DATA)
