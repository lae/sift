import os

class Config(object):
    CURRENT_EVENT_ID = 1
    LADDER_LIMIT = 100
    DEBUG = False
    DATABASE_URI = "sqlite://:memory:"
    MEMCACHE_ENABLED = False
    MEMCACHE_KEY = 'sift'

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

config = {
    "development": "sift.config.DevelopmentConfig",
    "testing": "sift.config.TestingConfig",
    "default": "sift.config.Config"
}

def configure_app(app):
    config_name = os.getenv("FLASK_ENV", "development")
    if config_name not in config:
        app.config.from_object(config["default"])
    else:
        app.config.from_object(config[config_name])
    app.config.from_pyfile('config/%s.cfg' % config_name, silent=True)
