# -*- coding: utf-8 -*-
from .boot import sift
import psycopg2
import psycopg2.extras
from flask import g


def connect_db():
    """Connects to SIF DB"""
    conn = psycopg2.connect(sift.config['DATABASE_URI'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return cur

def get_db():
    """Opens a new DB connection if there isn't already one"""
    if not hasattr(g, 'pg_db'):
        g.pg_db = connect_db()
    return g.pg_db

@sift.teardown_appcontext
def close_db(error):
    """Closes the db connection"""
    if hasattr(g, 'pg_db'):
        g.pg_db.close()
