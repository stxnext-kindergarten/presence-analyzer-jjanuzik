# -*- coding: utf-8 -*-
"""
This module updates users.xml file
"""

import urllib

dane = urllib.urlopen('http://sargo.bolt.stxnext.pl/users.xml')
xml = open('/xml/users.xml', 'w')

data = dane.read()

dane.close()
