# -*- coding: utf-8 -*-
from flask import Flask
from .config import configure_app
from .reverse_proxy import ReverseProxied

sift = Flask(__name__.split('.')[0], instance_relative_config=True)
configure_app(sift)
sift.wsgi_app = ReverseProxied(sift.wsgi_app)
