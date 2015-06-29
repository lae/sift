# -*- coding: utf-8 -*-
import os
import json
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from .boot import sift
from .blobs import *

@sift.teardown_appcontext
def close_db(error):
    """Closes the db connection"""
    if hasattr(g, 'pg_db'):
        g.pg_db.close()

@sift.route('/')
def index():
    page = 0
    event_id = sift.config['CURRENT_EVENT_ID']
    limit = sift.config['LADDER_LIMIT']
    data = Ranking().get(event_id, limit, page)
    if not data:
        abort(404)
    split_data = [data[i*limit//4: (i+1)*limit//4] for i in range(4)]
    return render_template('list_rankings.html', data=split_data, page=page, event_id=event_id)

@sift.route('/ranking/<int:event_id>')
def list_rankings(event_id):
    if 'page' in request.args:
        page = int(request.args['page'])
    else:
        page = 0

    limit = sift.config['LADDER_LIMIT']
    data = Ranking().get(event_id, limit, page)
    if not data:
        abort(404)
    split_data = [data[i*limit//4: (i+1)*limit//4] for i in range(4)]
    return render_template('list_rankings.html', data=split_data, page=page, event_id=event_id)

@sift.route('/history/<int:event_id>/user/<int:user_id>')
def history_user(event_id, user_id):
    data = HistoryUser().get(event_id, user_id)
    if not data:
        abort(404)
    entries = len(data)
    if entries < 20:
        column_count = 1
    elif entries <= 40:
        column_count = 2
    else:
        column_count = 3
    split_data = [data[i*entries//column_count: (i+1)*entries//column_count] for i in range(column_count)]
    return render_template('history.user.html', data=split_data, event_id=event_id, column_count=column_count)

@sift.route('/history/<int:event_id>/rank/<int:rank>')
def history_rank(event_id, rank):
    data = HistoryRank().get(event_id, rank)
    if not data:
        abort(404)
    entries = len(data)
    if entries < 20:
        column_count = 1
    elif entries <= 40:
        column_count = 2
    else:
        column_count = 4
    split_data = [data[i*entries//column_count: (i+1)*entries//column_count] for i in range(column_count)]
    return render_template('history.rank.html', data=split_data, event_id=event_id, rank=rank, column_count=column_count)

@sift.route('/cutoff/<int:event_id>')
def list_cutoffs(event_id):
    data = list(reversed(Cutoff().get(event_id, sift.config['CURRENT_EVENT_CUTOFF_MARKS'])))
    if not data:
        abort(404)
    return render_template('list_cutoffs.html', data=data, event_id=event_id)

@sift.route('/search')
def search():
    if 'q' in request.args:
        query = request.args['q']
        if len(query) < 2 or '%' in query:
            abort(418)
    else:
        abort(404)

    if 'event' in request.args:
        event_id = int(request.args['event'])
    else:
        event_id = sift.config['CURRENT_EVENT_ID']

    data = SearchUser().get(event_id, query)
    if not data:
        data = []
    return render_template('search_results.html', data=data, query=query, event_id=event_id)


class Revision(object):
    def revision(self):
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip().decode("utf-8")

    def on_get(self, req, resp):
        resp.body = json.dumps({"revision": self.revision()})

#api = application = falcon.API(middleware = ReverseProxy())

if __name__ == '__main__':
    app.run()
