# -*- coding: utf-8 -*-
from dogpile.cache import make_region
from .utils import get_db

region = make_region().configure(
    'dogpile.cache.pylibmc',
    expiration_time = 600,
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

class SearchUser(object):
    @region.cache_on_arguments()
    def get(self, event_id, search):
        c = get_db()
        c.execute("SELECT event_id, rank, user_id, name FROM rankings WHERE event_id = %(event_id)s AND step = (SELECT MAX(step) FROM rankings WHERE event_id = %(event_id)s) AND lower(name) LIKE %(search)s ORDER BY rank", {'event_id': event_id, 'search': '%'+search.lower()+'%'})
        results = c.fetchall()
        return results

class HistoryUser(object):
    @region.cache_on_arguments()
    def get(self, event_id, user_id):
        c = get_db()
        c.execute("SELECT step,rank,name,score FROM rankings WHERE event_id = %(event_id)s AND user_id = %(user_id)s ORDER BY step", {'event_id': event_id, 'user_id': user_id})
        history = c.fetchall()
        return history

class HistoryRank(object):
    @region.cache_on_arguments()
    def get(self, event_id, rank):
        c = get_db()
        c.execute("SELECT s.* FROM (SELECT * FROM generate_series(0, (SELECT max(step) FROM rankings WHERE event_id = %(event_id)s))) v(desired_step), lateral (SELECT step, score, name FROM rankings WHERE event_id = %(event_id)s AND rank <= %(rank)s AND step = desired_step ORDER BY rank DESC LIMIT 1) s ORDER BY s.step", {'event_id': event_id, 'rank': rank})
        history = c.fetchall()
        return history

class Cutoff(object):
    @region.cache_on_arguments()
    def get(self, event_id, cutoff_marks):
        c = get_db()
        c.execute("SELECT desired_rank, s.* FROM unnest(%(ranks)s) u(desired_rank), (SELECT * FROM generate_series((SELECT max(step) FROM rankings WHERE event_id = %(event_id)s)-24, (SELECT max(step) FROM rankings WHERE event_id = %(event_id)s))) v(desired_step), lateral (SELECT step, score, name FROM rankings WHERE event_id = %(event_id)s AND rank <= desired_rank AND step = desired_step ORDER BY rank DESC LIMIT 1) s ORDER BY s.step", {'event_id': event_id, 'ranks': cutoff_marks})
        results = c.fetchall()
        cutoffs = [{"step": step} for step in set(sorted([item['step'] for item in results]))]
        for item in results:
            tier = "tier_{}".format(cutoff_marks.index(int(item['desired_rank'])))
            score = item['score']
            step = item['step']
            name = item['name']
            for s in cutoffs:
                if s['step'] == step:
                    s[tier] = score
                    s[tier+'_name'] = name
        cutoffs = sorted(cutoffs, key=lambda cutoff: cutoff["step"])
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
