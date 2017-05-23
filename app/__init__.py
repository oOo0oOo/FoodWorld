from flask import Flask, Blueprint
from flask_ask import Ask

from flask_sqlalchemy import SQLAlchemy
from config import config

# Extensions
db = SQLAlchemy()
alexa = Ask(route = '/')

# Main blueprint
main = Blueprint('main', __name__)

from . import models, views

def create_app(config_name = 'development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    alexa.init_app(app)

    from . import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app