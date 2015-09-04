"""
Connect to an ElasticSearch cluster containing log data (e.g.  our
logs-elasticsearch cluster) and dump records matching a specified query in CSV
format.

e.g. dump the fields "@fields.request" and "@fields.request_time" for all log
     entries matching the query

         @fields.application:whitehall-admin AND @tags:nginx

     from dates between midnight on 2013-05-13 and midnight on 2013-05-20:

         python logdump.py --from 2013-05-13T00:00:00Z \
                           --to 2013-05-20T00:00:00Z \
                           --fields @fields.request @fields.request_time \
                           --query '@fields.application:whitehall-admin AND @tags:nginx'
"""
import argparse
import csv
import datetime
import functools
import json
import sys

import requests

BATCH_SIZE = 200
DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"
ES_ROOT = 'http://127.0.0.1:9200'

class LogQuery(object):

    def __init__(self, query, date_from, date_to, fields=None, index='logs'):
        self.query = query
        self.date_from = date_from
        self.date_to = date_to
        self.fields = fields
        self.index = index

    def results(self):
        days = (self.date_to - self.date_from).days

        for i in range(days + 1):
            for item in self._results_for_day(i):
                yield item

    def _results_for_day(self, day):
        index_date = self.date_from + datetime.timedelta(days=day)
        index_name = self.index + '-' + index_date.strftime('%Y.%m.%d')

        payload = {
            'query': self._build_query(),
            'size': BATCH_SIZE,
            'sort': [{ '@timestamp': 'asc' }],
        }
        if self.fields:
            payload['fields'] = self.fields

        req = functools.partial(requests.get,
                                ES_ROOT + '/' + index_name + '/_search')

        read = 0
        while True:
            payload['from'] = read

            resp = req(data=json.dumps(payload))
            resp.raise_for_status()

            data = resp.json()

            for item in data['hits']['hits']:
                read += 1
                if self.fields:
                    yield {k: ','.join(v) for k, v in item['fields'].items()}
                else:
                    result = {}
                    for k, v in item['_source'].items():
                        if isinstance(v, basestring):
                            result[k] = v
                        else:
                            result[k] = json.dumps(v)
                    yield result

            if data['hits']['total'] <= read:
                break

    def _build_query(self):
        q_query = {
            'query_string': {
                'default_operator': 'OR',
                'default_field': '@message',
                'query': self.query,
            }
        }
        q_filter = {
            'range': {
                '@timestamp': {
                    'from': self.date_from.strftime(DATE_FMT),
                    'to': self.date_to.strftime(DATE_FMT),
                }
            }
        }
        q = {
            'filtered': {
                'query': q_query,
                'filter': q_filter,
            }
        }
        return q
