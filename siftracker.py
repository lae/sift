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
    expiration_time = 300,
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

class FourChanners(object):
    def __init__(self):
        self.members = (65,115,242,272,393,468,612,727,852,895,1007,1133,1228,1569,2223,2284,2658,2701,3231,3350,3383,3677,3892,3965,4020,4109,4255,4426,4523,4732,5250,5324,5378,5724,5911,5993,6047,6096,6464,6676,6763,7085,7249,7531,7578,7605,7894,8020,8071,8153,8427,8654,8772,8919,9133,9192,9254,9455,9540,9621,9755,10370,10706,11847,12638,12801,13190,13219,13615,16084,18927,19169,19189,19554,23385,24353,25431,27677,28502,30184,30409,31321,33187,33501,34256,35976,36193,43753,45865,47383,47507,48469,49397,53330,54407,54442,54726,56998,57171,59114,59156,62517,63456,64203,67585,71148,72776,73051,77122,85386,88081,90819,92967,94117,94582,99710,104518,107266,110126,118533,118654,127679,129038,131215,132159,135023,135142,135470,138327,138517,142738,143817,144169,147942,147955,152290,153411,156666,157967,158338,160339,162052,164670,169040,171951,177062,177768,178357,184574,185582,188457,189259,191472,197233,204027,209570,215952,224043,228746,229359,231763,235266,235686,241579,243766,245293,249413,256156,256655,259316,274227,274312,278283,278967,279011,283604,284027,290863,300793,310065,318164,318236,321161,323174,340046,353611,361654,363427,363729,375591,376526,377257,384046,404882,407495,418600,430112,437719,445818,446500,457151,464594,467497,469946,479490,480615,484897,485651,486662,491094,492435,499568,508660,508964,509791,511503,516729,518555,519251,519251,523888,525487,537409,543298,551263,592525,593969,594418,622510,641106,642235,648489,649749,653232,655076,658931,669983,683311,686229,693777,714813,719428,736040,738428,744739,758627,760940,762567,778511,782198,793476,794897,797155,808253,814764,819125,842274,850445,862487,870444,879882,888680,897325,904110,908289,918041,936224,941208,946825,955849,961224,966327,969077,975041,1000369,1040239,1085141,1087773,1133970,1133970,1147131,1166294,1232585,1277954,515636250,764673408)

    @region.cache_on_arguments()
    def get_rankings(self, event_id):
        c = new_cursor()
        c.execute("SELECT rank,name,user_id,score FROM rankings WHERE event_id = %(event_id)s AND step = (SELECT MAX(step) FROM rankings WHERE event_id = %(event_id)s) AND user_id IN %(members)s ORDER BY rank", {'event_id': event_id, 'members': self.members})
        rankings = c.fetchall()
        return rankings

    def on_get(self, req, resp, event_id):
        rankings = self.get_rankings(event_id)
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
        c.execute("SELECT desired_rank, s.* FROM unnest(%(ranks)s) u(desired_rank), (SELECT * FROM generate_series(0, (SELECT max(step) FROM rankings WHERE event_id = %(event_id)s))) v(desired_step), lateral (SELECT step, score FROM rankings WHERE event_id = %(event_id)s AND rank <= desired_rank AND step = desired_step ORDER BY rank DESC LIMIT 1) s ORDER BY s.step", {'event_id': event_id, 'ranks': cutoff_marks})
        results = c.fetchall()
        return results

    def on_get(self, req, resp, event_id):
        #cutoff_marks = (1,600,3000,6000,12000)
#        c.execute("SELECT step,rank,score FROM rankings WHERE event_id = %(event_id)s AND rank IN %(ranks)s", {'event_id': event_id, 'ranks': cutoff_marks})
        cutoff_marks = [1,800,4000,8000,16000]
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
api.add_route('/yonchanneru/{event_id}', FourChanners())
api.add_route('/revision', Revision())
