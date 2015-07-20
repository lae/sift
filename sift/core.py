# -*- coding: utf-8 -*-
import os
import json
import collections
import math
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from .boot import sift
from .blobs import *


@sift.context_processor
def event_menu():
    events = EventMeta().get_all()
    event_menu = collections.OrderedDict()
    for event in events:
        group = "Round %s" % event['round']
        event_item = {
            'id': event['event_id'],
            'name': event['name']
        }
        if group not in event_menu:
            event_menu[group] = [event_item]
        else:
            event_menu[group].append(event_item)
    return dict(event_menu=event_menu)

@sift.context_processor
def get_revision():
    return dict(revision=Revision().get())

@sift.route('/')
def index():
    page = 0
    event_id = sift.config['CURRENT_EVENT_ID']
    limit = sift.config['LADDER_LIMIT']

    event_info = EventMeta().get(event_id)
    if not event_info:
        abort(404)

    data = Ranking().get(event_id, limit, page)
    if not data:
        return render_template(
            'event_not_started.html',
            event = event_info[0]
        )

    split_data = [data[i*limit//4: (i+1)*limit//4] for i in range(4)]
    return render_template(
        'list_rankings.html',
        data = split_data,
        page = page,
        event = event_info[0]
    )

@sift.route('/ranking/<int:event_id>')
def list_rankings(event_id):
    if 'page' in request.args:
        page = int(request.args['page'])
    else:
        page = 0

    limit = sift.config['LADDER_LIMIT']

    event_info = EventMeta().get(event_id)
    if not event_info:
        abort(404)

    data = Ranking().get(event_id, limit, page)
    if not data:
        if event_id == sift.config['CURRENT_EVENT_ID']:
            return render_template(
                'event_not_started.html',
                event = event_info[0]
            )
        else:
            abort(404)

    split_data = [data[i*limit//4: (i+1)*limit//4] for i in range(4)]
    return render_template(
        'list_rankings.html',
        data = split_data,
        page = page,
        event = event_info[0]
    )

@sift.route('/history/<int:event_id>/user/<int:user_id>')
def history_user(event_id, user_id):
    event_info = EventMeta().get(event_id)
    if not event_info:
        abort(404)

    user_info = UserMeta().get(user_id)
    if not user_info:
        abort(404)

    valid_events = HistoryUserEvents().get(user_id)
    if not valid_events or event_id not in valid_events:
        abort(404)

    data = HistoryUser().get(event_id, user_id)
    if not data:
        abort(404)

    entries = len(data)
    if entries < 20:
        column_count = 1
    elif entries <= 40:
        column_count = 2
    else:
        column_count = 4

    split_data = [data[math.ceil(i*entries/column_count): math.ceil((i+1)*entries/column_count)] for i in range(column_count)]
    return render_template(
        'history.user.html',
        data = split_data,
        user_id = user_id,
        column_count = column_count,
        filter_events = valid_events,
        event = event_info[0],
        user = user_info[0]
    )

@sift.route('/history/user/<int:user_id>')
def history_user_events(user_id):
    event_id = sift.config['CURRENT_EVENT_ID']

    event_info = EventMeta().get(event_id)
    if not event_info:
        # Current event should always exist and this won't be a client error
        abort(500)

    valid_events = HistoryUserEvents().get(user_id)
    if not valid_events:
        abort(404)

    data = HistoryUser().get(user_id)
    if not data:
        abort(404)


    return render_template(
        'history.user.html',
        data = data,
        user_id = user_id,
        filter_events = valid_events
    )


@sift.route('/history/<int:event_id>/rank/<int:rank>')
def history_rank(event_id, rank):
    event_info = EventMeta().get(event_id)
    if not event_info:
        abort(404)

    data = HistoryRank().get(event_id, rank)
    if not data:
        if event_id == sift.config['CURRENT_EVENT_ID']:
            return render_template(
                'event_not_started.html',
                event = event_info[0]
            )
        else:
            abort(404)

    entries = len(data)
    if entries < 20:
        column_count = 1
    elif entries <= 40:
        column_count = 2
    else:
        column_count = 4
    split_data = [data[i*entries//column_count: (i+1)*entries//column_count] for i in range(column_count)]
    return render_template(
        'history.rank.html',
        data = split_data,
        rank = rank,
        column_count = column_count,
        event = event_info[0]
    )

@sift.route('/cutoff/<int:event_id>')
def list_cutoffs(event_id):
    event_info = EventMeta().get(event_id)
    if not event_info:
        abort(404)

    borders = [1] + event_info[0]['borders'][0:5]
    tiers = list(range(0, len(borders)))

    data = Cutoff().get(event_id, borders)
    data = list(reversed(data))
    if not data:
        if event_id == sift.config['CURRENT_EVENT_ID']:
            return render_template(
                'event_not_started.html',
                event = event_info[0]
            )
        else:
            abort(404)

    return render_template(
        'list_cutoffs.html',
        tiers = tiers,
        data = data,
        borders = borders,
        event = event_info[0]
    )

@sift.route('/search')
def search():
    if 'q' in request.args:
        query = request.args['q']
        if len(query) == 0 or '%' in query:
            abort(418)
    else:
        abort(404)

    if 'event' in request.args:
        event_id = int(request.args['event'])
    else:
        event_id = sift.config['CURRENT_EVENT_ID']

    event_info = EventMeta().get(event_id)
    if not event_info:
        abort(404)

    data = SearchUser().get(event_id, query)
    if not data:
        data = []
    return render_template(
        'search_results.html',
        data = data,
        query = query,
        event = event_info[0]
    )


if __name__ == '__main__':
    app.run()
