# -*- coding: utf-8 -*-
from dogpile.cache import make_region
from .utils import get_db

region = make_region().configure(
    'dogpile.cache.pylibmc',
    expiration_time = 300,
    arguments = {
        'url':["127.0.0.1:11211"],
        'binary': True,
        'behaviors':{"tcp_nodelay": True,"ketama":True}
    }
)

class Ranking(object):
    def __init__(self):
        self.default_limit = 100
        self.max_limit = 1000

    @region.cache_on_arguments()
    def get(self, event_id, limit, page):
        c = get_db()
        c.execute("SELECT rank,name,user_id,score FROM rankings WHERE event_id = %(event_id)s AND step = (SELECT MAX(step) FROM rankings WHERE event_id = %(event_id)s) ORDER BY rank LIMIT %(limit)s OFFSET %(offset)s", {'event_id': event_id, 'limit': limit, 'offset': page * limit})
        rankings = c.fetchall()
        return rankings

class HistoryUser(object):
    @region.cache_on_arguments()
    def get(self, event_id, user_id):
        c = get_db()
        c.execute("SELECT step,rank,name,score FROM rankings WHERE event_id = %(event_id)s AND user_id = %(user_id)s ORDER BY step", {'event_id': event_id, 'user_id': user_id})
        history = c.fetchall()
        return history

class Cutoff(object):
    @region.cache_on_arguments()
    def get(self, event_id, cutoff_marks):
        c = get_db()
        c.execute("SELECT desired_rank, s.* FROM unnest(%(ranks)s) u(desired_rank), (SELECT * FROM generate_series(0, (SELECT max(step) FROM rankings WHERE event_id = %(event_id)s))) v(desired_step), lateral (SELECT step, score FROM rankings WHERE event_id = %(event_id)s AND rank <= desired_rank AND step = desired_step ORDER BY rank DESC LIMIT 1) s ORDER BY s.step", {'event_id': event_id, 'ranks': cutoff_marks})
        results = c.fetchall()
        cutoffs = [{"step": step} for step in set(sorted([item['step'] for item in results]))]
        for item in results:
            tier = "tier_{}".format(cutoff_marks.index(int(item['desired_rank'])))
            score = item['score']
            step = item['step']
            for s in cutoffs:
                if s['step'] == step:
                    s[tier] = score
        return cutoffs


"""
class HistoryUserEvents(object):
    @region.cache_on_arguments(expiration_time=14400)
    def get_history_user_events(self, user_id):
        c = new_cursor()
        c.execute("SELECT s.* FROM (SELECT * FROM generate_series(3, (SELECT max(event_id) FROM rankings))) u(ev), lateral (SELECT event_id FROM rankings WHERE event_id = ev AND user_id = %(user_id)s LIMIT 1) s", {'user_id': user_id})
        events = c.fetchall()
        return events

    def on_get(self, req, resp, user_id):
"""
