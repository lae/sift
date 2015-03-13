#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import falcon
import os
import json
import psycopg2
import psycopg2.extras
from dogpile.cache import make_region

def new_cursor():
    conn = psycopg2.connect("dbname=sifentracker host=/tmp")
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return cur

region = make_region().configure(
    'dogpile.cache.pylibmc',
    expiration_time = 900,
    arguments = {
        'url':["127.0.0.1:11211"],
        'binary': True,
        'behaviors':{"tcp_nodelay": True,"ketama":True}
    }
)

class ReverseProxy(object):
    def process_request(self, req, resp, **params):
        script_name = req.get_header('X-Script-Name')
        if script_name:
            path = req.path
            if path.startswith(script_name):
                req.path = path[len(script_name):]

class Ranking(object):
    def __init__(self):
        self.default_limit = 100
        self.max_limit = 1000

    @region.cache_on_arguments()
    def get_rankings(self, event_id, limit, page):
        c = new_cursor()
        c.execute("SELECT rank,name,user_id,score FROM rankings WHERE event_id = %(event_id)s AND step = (SELECT MAX(step) FROM rankings WHERE event_id = %(event_id)s) ORDER BY rank LIMIT %(limit)s OFFSET %(offset)s", {'event_id': event_id, 'limit': limit, 'offset': page * limit})
        rankings = c.fetchall()
        return rankings

    def on_get(self, req, resp, event_id):
        limit = req.get_param_as_int('limit') or self.default_limit
        if limit > self.max_limit or limit <= 0:
            raise falcon.HTTPBadRequest('Limit Out of Range', 'limit parameter' \
                    ' must be greater than 0 and less than or equal to {}.'
                    .format(self.max_limit))
        page = req.get_param_as_int('page') or 0
        if page < 0:
            raise falcon.HTTPBadRequest('Page Out of Range', 'page parameter' \
                    ' must be greater than or equal to 0.')
        rankings = self.get_rankings(event_id, limit, page)
        if not rankings:
            raise falcon.HTTPNotFound()
        resp.body = json.dumps(rankings)

class HistoryUser(object):
    @region.cache_on_arguments()
    def get_history_user(self, event_id, user_id):
        c = new_cursor()
        c.execute("SELECT step,rank,name,score FROM rankings WHERE event_id = %(event_id)s AND user_id = %(user_id)s ORDER BY step", {'event_id': event_id, 'user_id': user_id})
        history = c.fetchall()
        return history

    def on_get(self, req, resp, event_id, user_id):
        history = self.get_history_user(event_id, user_id)
        if not history:
            raise falcon.HTTPNotFound()
        resp.body = json.dumps(history)

class HistoryUserEvents(object):
    @region.cache_on_arguments(expiration_time=14400)
    def get_history_user_events(self, user_id):
        c = new_cursor()
        c.execute("SELECT s.* FROM (SELECT * FROM generate_series(3, (SELECT max(event_id) FROM rankings))) u(ev), lateral (SELECT event_id FROM rankings WHERE event_id = ev AND user_id = %(user_id)s LIMIT 1) s", {'user_id': user_id})
        events = c.fetchall()
        return events

    def on_get(self, req, resp, user_id):
        events = self.get_history_user_events(user_id)
        if not events:
            raise falcon.HTTPNotFound()
        events = [e["event_id"] for e in events]
        resp.body = json.dumps(events)

class Cutoff(object):
    @region.cache_on_arguments()
    def get_cutoffs(self, event_id, cutoff_marks):
        c = new_cursor()
        c.execute("SELECT desired_rank, s.* FROM unnest(%(ranks)s) u(desired_rank), (SELECT * FROM generate_series(0, (SELECT max(step) FROM rankings WHERE event_id = %(event_id)s))) v(desired_step), lateral (SELECT step, score FROM rankings WHERE event_id = %(event_id)s AND rank <= desired_rank AND step = desired_step ORDER BY rank DESC LIMIT 1) s", {'event_id': event_id, 'ranks': cutoff_marks})
        results = c.fetchall()
        return results

    def on_get(self, req, resp, event_id):
        #cutoff_marks = (1,600,3000,6000,12000)
#        c.execute("SELECT step,rank,score FROM rankings WHERE event_id = %(event_id)s AND rank IN %(ranks)s", {'event_id': event_id, 'ranks': cutoff_marks})
        cutoff_marks = [1,600,3000,6000,12000]
        results = self.get_cutoffs(event_id, cutoff_marks)
        if not results:
            raise falcon.HTTPNotFound()
        cutoffs = [{"step": step} for step in set(sorted([item['step'] for item in results]))]
        for item in results:
            tier = "tier_{}".format(cutoff_marks.index(int(item['desired_rank'])))
            score = item['score']
            step = item['step']
            for s in cutoffs:
                if s['step'] == step:
                    s[tier] = score
        resp.body = json.dumps(cutoffs)

class Revision(object):
    def revision(self):
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip().decode("utf-8")

    def on_get(self, req, resp):
        resp.body = json.dumps({"revision": self.revision()})

api = application = falcon.API(middleware = ReverseProxy())
api.add_route('/ranking/{event_id}', Ranking())
api.add_route('/cutoff/{event_id}', Cutoff())
api.add_route('/history_user/{event_id}/{user_id}', HistoryUser())
api.add_route('/history_user_events/{user_id}', HistoryUserEvents())
api.add_route('/revision', Revision())
