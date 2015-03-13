#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import falcon
import os
import json
import psycopg2
import psycopg2.extras

def new_cursor():
    conn = psycopg2.connect("dbname=sifentracker host=/tmp")
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return cur

class ReverseProxy(object):
    def process_request(self, req, resp, **params):
        script_name = req.get_header('X-Script-Name')
        if script_name:
            path = req.path
            if path.startswith(script_name):
                req.path = path[len(script_name):]

class Ranking(object):
    def on_get(self, req, resp, event_id):
        limit = req.get_param_as_int('limit') or 100
        if limit > 1000 or limit <= 0:
            raise falcon.HTTPBadRequest('Limit Out of Range', 'limit parameter' \
                    ' must be greater than 0 and less than or equal to 1000.')
        page = req.get_param_as_int('page') or 0
        if page < 0:
            raise falcon.HTTPBadRequest('Page Out of Range', 'page parameter' \
                    ' must be greater than or equal to 0.')
        c = new_cursor()
        c.execute("SELECT rank,name,user_id,score FROM rankings WHERE event_id = %(event_id)s AND step = (SELECT MAX(step) FROM rankings WHERE event_id = %(event_id)s) ORDER BY rank LIMIT %(limit)s OFFSET %(offset)s", {'event_id': event_id, 'limit': limit, 'offset': page * limit})
        rankings = c.fetchall()
        if not rankings:
            raise falcon.HTTPNotFound()
        resp.body = json.dumps(rankings)

class HistoryUser(object):
    def on_get(self, req, resp, event_id, user_id):
        c = new_cursor()
        c.execute("SELECT step,rank,name,score FROM rankings WHERE event_id = %(event_id)s AND user_id = %(user_id)s ORDER BY step", {'event_id': event_id, 'user_id': user_id})
        history = c.fetchall()
        if not history:
            raise falcon.HTTPNotFound()
        resp.body = json.dumps(history)

class Cutoff(object):
    def on_get(self, req, resp, event_id):
        cutoff_marks = (1,600,3000,6000,12000)
        c = new_cursor()
        c.execute("SELECT step,rank,score FROM rankings WHERE event_id = %(event_id)s AND rank IN %(ranks)s", {'event_id': event_id, 'ranks': cutoff_marks})
        results = c.fetchall()
        if not results:
            raise falcon.HTTPNotFound()
        cutoffs = [{"step": step} for step in set(sorted([item['step'] for item in results]))]
        for item in results:
            tier = "tier_{}".format(cutoff_marks.index(int(item['rank'])))
            score = item['score']
            step = item['step']
            for s in cutoffs:
                if s['step'] == step:
                    s[tier] = score
        resp.body = json.dumps(cutoffs)

class Revision(object):
    def __init__(self):
        import subprocess
        self.revision = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip().decode("utf-8")

    def on_get(self, req, resp):
        resp.body = json.dumps({"revision": self.revision})

api = application = falcon.API(middleware = ReverseProxy())
api.add_route('/ranking/{event_id}', Ranking())
api.add_route('/cutoff/{event_id}', Cutoff())
api.add_route('/history_user/{event_id}/{user_id}', HistoryUser())
api.add_route('/revision', Revision())
