# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=E1103
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests
    """

    def setUp(self):
        """
        Before each test, set up a environment
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_mean_time_weekday_view(self):
        """
        Test mean presence time of given users.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertListEqual(
            data,
            [
                [u'Mon', 0],
                [u'Tue', 30047.0],
                [u'Wed', 24465.0],
                [u'Thu', 23705.0],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0]
            ],
        )

    def test_pesence_weekday_view(self):
        """
        Test presence weekday view.
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertListEqual(
            data,
            [
                [u'Weekday', u'Presence (s)'],
                [u'Mon', 0],
                [u'Tue', 30047],
                [u'Wed', 24465],
                [u'Thu', 23705],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0],
            ],
        )

    def test_presence_start_end(self):
        """
        Testing presence start and end
        """
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertListEqual(
            data,
            [
                [u'Mon', 0, 0],
                [u'Tue', 34745.0, 64792.0],
                [u'Wed', 33592.0, 58057.0],
                [u'Thu', 38926.0, 62631.0],
                [u'Fri', 0, 0],
                [u'Sat', 0, 0],
                [u'Sun', 0, 0],
            ],
        )


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """
    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(data[10][sample_date]['start'],
                         datetime.time(9, 39, 5))

    def test_mean(self):
        """
        Testing if mean function calculates correctly.
        """
        self.assertEqual(
            utils.mean([3, 4, 5]), 4
        )
        self.assertEqual(
            utils.mean([]), 0
        )
        self.assertAlmostEqual(
            utils.mean([12.7, 20.5, 16.5]),
            16.56666666,
        )

    def test_seconds_since_midnight(self):
        """
        Testing seconds since midnight.
        """
        self.assertEqual(
            utils.seconds_since_midnight(datetime.time(12, 35, 0)),
            45300,
        )
        self.assertEqual(
            utils.seconds_since_midnight(datetime.time(15, 40, 0)),
            56400,
        )

    def test_interval(self):
        """
        Testing interval function.
        """
        self.assertEqual(
            utils.interval(
                (datetime.time(12, 30, 00)),
                (datetime.time(12, 30, 15)),
            ),
            15,
        )

    def test_group_by_weekday(self):
        """
        Testing group presence during weekday.
        """
        self.assertDictEqual(
            utils.group_by_weekday(utils.get_data()[10]),
            {
                0: [],
                1: [30047],
                2: [24465],
                3: [23705],
                4: [],
                5: [],
                6: [],
            },
        )

    def test_group_by_weekday_in_secs(self):
        """
        Testingpresence during weekday in seconds including start and end
        """
        self.assertDictEqual(
            utils.group_by_weekday_in_secs(utils.get_data()[10]),
            {
                0: {'end': [], 'start': []},
                1: {'end': [64792], 'start': [34745]},
                2: {'end': [58057], 'start': [33592]},
                3: {'end': [62631], 'start': [38926]},
                4: {'end': [], 'start': []},
                5: {'end': [], 'start': []},
                6: {'end': [], 'start': []},
            },
        )


def suite():
    """
    Default test suite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
