# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import redirect, render_template, url_for

from presence_analyzer.main import app
from presence_analyzer.utils import(
    jsonify,
    get_data, mean, group_by_weekday,
    group_by_weekday_in_secs,
)
from flask.helpers import make_response

from jinja2 import exceptions

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect(
        url_for('template_view', template_name='presence_weekday')
    )


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [{'user_id': i, 'name': 'User {0}'.format(str(i))}
            for i in data.keys()]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], mean(intervals))
              for weekday, intervals in weekdays.items()]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], sum(intervals))
              for weekday, intervals in weekdays.items()]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end(user_id):
    """
    Returns mean presence time of given user
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday_in_secs(data[user_id])
    result = [(calendar.day_abbr[weekday],
              mean(mean_per_day['start']),
              mean(mean_per_day['end']))
              for weekday, mean_per_day in weekdays.items()]
    return result


@app.route('/<string:template_name>', methods=['GET'])
def template_view(template_name):
    """
    Renders webside
    """
    try:
        return render_template("{}.html".format(template_name))
    except exceptions.TemplateNotFound:
        return make_response("Strona o podanym adresie nie istnieje")
