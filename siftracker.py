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

api = application = falcon.API(middleware = ReverseProxy())
api.add_route('/ranking/{event_id}', Ranking())
api.add_route('/history_user/{event_id}/{user_id}', HistoryUser())
