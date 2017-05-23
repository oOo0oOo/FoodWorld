import os

from app import create_app

# Create an application instance that web servers can use.
# TODO: make this production!!
application = app = create_app('development')