# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import xml
import urllib2
import time
import threading
from json import dumps
from functools import wraps
from datetime import datetime
from lxml import etree
from flask import Response
import logging

log = logging.getLogger(__name__)  # pylint: disable-msg=C0103

from presence_analyzer.main import app
CACHE = {}
TIMESTAMPS = {}
LOCKER = threading.Lock()


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        return Response(dumps(function(*args, **kwargs)),
                        mimetype='application/json')
    return inner


def cache(key, seconds):
    """
    Cache
    """
    def _cache(function):
        def __cache(*args, **kwargs):
            """
            Function that checks if we have already cached items or not
            If we do, it returns cached items, if not adds them to cache dict.
            """
            now = datetime.now()
            timestamp = time.mktime(now.timetuple())
            if key in CACHE:
                if timestamp < TIMESTAMPS.get(key, 0):
                    return CACHE[key]

            result = function(*args, **kwargs)
            CACHE[key] = result
            expired_timestamp = timestamp + seconds
            TIMESTAMPS[key] = expired_timestamp
            return CACHE[key]

        return __cache
    return _cache


def locking(function):
    """
    Decorator used for multi-threading
    """
    def __locking(*args, **kwargs):
        """
        Locker used for multi-threading
        """
        with LOCKER:
            result = function(*args, **kwargs)
            return result
    return __locking


@locking
@cache(key='user_id', seconds=10)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = {i: [] for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def group_by_weekday_in_secs(items):
    """
    Groups presence entries by weekday.
    """
    result = {i: {'start': [], 'end': []} for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()]['start'].append(seconds_since_midnight(start))
        result[date.weekday()]['end'].append(seconds_since_midnight(end))
    return result


def parse_users_xml():
    """
    Parses user information
    """
    with open(app.config['DATA_XML'], 'r') as xmlfile:
        tree = etree.parse(xmlfile)
        server = tree.find('server')
        host = server.find('host').text
        protocol = server.find('protocol').text
        users_element = tree.find('users')
        result = {
            int(user.get('id')): {
                'name': user.find('name').text,
                'avatar': "{protocol}://{host}{avatar}".format(
                    protocol=protocol,
                    host=host,
                    avatar=user.find('avatar').text
                    )
            } for user in users_element
        }
    return result


def update_xml_file():
    """
    Updates users.xml file
    """
    with open(app.config['DATA_XML'], 'w+') as xmlfile:
        response = urllib2.urlopen(app.config['XML_SOURCE'])
        new_data = response.read()
        xmlfile.write(new_data)
