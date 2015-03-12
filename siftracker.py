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


api = application = falcon.API()
ranking = Ranking()
api.add_route('/ranking/{event_id}', ranking)
