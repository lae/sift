# -*- coding: utf-8 -*-
import os
import json
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from .reverse_proxy import ReverseProxied
from .blobs import *

sift = Flask(__name__)
sift.wsgi_app = ReverseProxied(sift.wsgi_app)
sift.config.from_object(__name__)

# Load default config and override config from an environment variable
sift.config.update(dict(
    SECRET_KEY='GwqqNjR7m2jU8rTosPUFhu9HH1tBf51nhBg1t914nSXgj1uEMIu2veeS3AezL4zB',
    USERNAME='lae',
    PASSWORD='idk',
    CURRENT_EVENT_ID=50
))

@sift.teardown_appcontext
def close_db(error):
    """Closes the db connection"""
    if hasattr(g, 'pg_db'):
        g.pg_db.close()

@sift.route('/')
def index():
#    page = req.get_param_as_int('page') or 0
#    if page < 0:
#        raise falcon.HTTPBadRequest('Page Out of Range', 'page parameter' \
#                ' must be greater than or equal to 0.')
    page = 0
    event_id = 50
    limit = 100
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

    limit = 100
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
    split_data = [data[i*entries//4: (i+1)*entries//4] for i in range(4)]
    return render_template('history.user.html', data=split_data, event_id=event_id)

@sift.route('/cutoff/<int:event_id>')
def list_cutoffs(event_id):
    cutoff_marks = [1,10000,50000,120000,250000]
    data = Cutoff().get(event_id, cutoff_marks)
    if not data:
        abort(404)
    return render_template('list_cutoffs.html', data=data, event_id=event_id)

class Revision(object):
    def revision(self):
        import subprocess
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip().decode("utf-8")

    def on_get(self, req, resp):
        resp.body = json.dumps({"revision": self.revision()})

#api = application = falcon.API(middleware = ReverseProxy())

if __name__ == '__main__':
    app.run()
