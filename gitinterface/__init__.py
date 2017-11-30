from flask import Flask, session
from flask.ext.dotenv import DotEnv
app = Flask(__name__)

class Config(object):
    TESTING = False
    env = DotEnv()
    env.init_app(app, verbose_mode=True)

class ProductionConfig(Config):
    DATABASE_URI = 'mysql://user@localhost/foo'

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

import gitinterface.views


if __name__ == '__main__':
    session.init_app(app)
    app.run(debug=True)
