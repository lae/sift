# -*- coding: utf-8 -*-
from .boot import sift
from dogpile.cache import make_region
from .utils import get_db


if sift.config['MEMCACHE_ENABLED']:
    region = make_region().configure(
        'dogpile.cache.pylibmc',
        expiration_time = 600,
        arguments = {
            'url':["127.0.0.1:11211"],
            'binary': True,
            'distributed_lock': True,
            'behaviors': {
                "tcp_nodelay": True,
                "ketama": True
            }
        }
    )
    # We use this to allow us to run multiple instances with separate databases
    # i.e. EN and JP need to use a separate cache
    if 'MEMCACHE_KEY' not in sift.config:
        region.key = 'sift'
    else:
        region.key = sift.config['MEMCACHE_KEY']
else:
    region = make_region().configure(
        'dogpile.cache.null'
    )
    region.key = "null"

class Ranking(object):
    def __init__(self):
        self.default_limit = 100
        self.max_limit = 1000

    @region.cache_on_arguments(namespace=region.key)
    def get(self, event_id, limit, page):
        c = get_db()
        c.execute(
            "SELECT rank,name,user_id,score FROM rankings " \
            "WHERE event_id = %(event_id)s AND step = " \
            "(SELECT MAX(step) FROM rankings WHERE event_id = %(event_id)s) " \
            "ORDER BY rank LIMIT %(limit)s OFFSET %(offset)s",
            {'event_id': event_id, 'limit': limit, 'offset': page * limit}
        )
        rankings = c.fetchall()
        return rankings

class SearchUser(object):
    @region.cache_on_arguments(namespace=region.key)
    def get(self, event_id, search):
        c = get_db()
        c.execute(
            "SELECT event_id, rank, user_id, name FROM rankings " \
            "WHERE event_id = %(event_id)s AND step = " \
                "(SELECT MAX(step) FROM rankings " \
                    "WHERE event_id = %(event_id)s) " \
                "AND lower(name) LIKE %(search)s " \
            "ORDER BY rank",
            {'event_id': event_id, 'search': '%'+search.lower()+'%'}
        )
        results = c.fetchmany(500)
        return results

class HistoryUser(object):
    @region.cache_on_arguments(namespace=region.key)
    def get(self, event_id, user_id):
        c = get_db()
        c.execute(
            "SELECT step,rank,name,score FROM rankings " \
            "WHERE event_id = %(event_id)s AND user_id = %(user_id)s " \
            "ORDER BY step",
            {'event_id': event_id, 'user_id': user_id}
        )
        history = c.fetchall()
        return history

class HistoryRank(object):
    @region.cache_on_arguments(namespace=region.key)
    def get(self, event_id, rank):
        c = get_db()
        c.execute(
            "SELECT s.* FROM (SELECT step FROM rankings_mv_playercount " \
                "WHERE event_id = %(event_id)s AND players >= %(rank)s " \
                "ORDER BY step) v(desired_step), " \
            "lateral (SELECT step, score, name FROM rankings " \
                "WHERE event_id = %(event_id)s AND rank <= %(rank)s " \
                "AND step = desired_step " \
                "ORDER BY rank DESC LIMIT 1) s " \
            "ORDER BY s.step",
            {'event_id': event_id, 'rank': rank}
        )
        history = c.fetchall()
        return history

class EventMeta(object):
    @region.cache_on_arguments(namespace=region.key)
    def get(self, event_id):
        c = get_db()
        c.execute(
            "SELECT * from event_meta WHERE event_id = %(event_id)s",
            {'event_id': event_id}
        )
        results = c.fetchall()
        return results

    @region.cache_on_arguments(namespace=region.key)
    def get_all(self):
        c = get_db()
        c.execute("SELECT * from event_meta ORDER BY id")
        results = c.fetchall()
        return results

class Cutoff(object):
    @region.cache_on_arguments(namespace=region.key)
    def get(self, event_id, cutoff_marks):
        c = get_db()
        c.execute(
            "SELECT sel_rank, s.* FROM unnest(%(ranks)s) u(sel_rank), " \
            # Grab a list of steps from selected event along with player count
            "(SELECT step, players FROM rankings_mv_playercount " \
                "WHERE event_id = %(event_id)s ORDER BY step) " \
                "v(sel_step, sel_step_players), " \
            # and then try to match the closest rank we want, since ties cause
            # duplicate rank numbers (and skips numbers), if the number of
            # players is greater than the rank we want
            "lateral (SELECT step, score, name FROM rankings " \
                "WHERE event_id = %(event_id)s AND rank <= sel_rank " \
                    "AND step = sel_step AND sel_rank <= sel_step_players " \
                "ORDER BY rank DESC LIMIT 1) s " \
            # and make sure we order by step (a.k.a. elapsed hours)
            "ORDER BY s.step",
            {'event_id': event_id, 'ranks': cutoff_marks}
        )
        results = c.fetchall()
        cutoffs = [{"step": step} for step in
                   set(sorted([item['step'] for item in results]))]
        for item in results:
            tier = "tier_{}".format(cutoff_marks.index(int(item['sel_rank'])))
            score = item['score']
            step = item['step']
            name = item['name']
            for s in cutoffs:
                if s['step'] == step:
                    s[tier] = score
                    s[tier+'_name'] = name
        cutoffs = sorted(cutoffs, key=lambda cutoff: cutoff["step"])
        return cutoffs


class Revision(object):
    def revision(self):
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip().decode("utf-8")

    def get(self):
        return self.revision()


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
