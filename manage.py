from flask_script import Manager, Command, Server as _Server, Option
from flask_script import prompt_bool

from app import create_app, db

app = create_app()
manager = Manager(app)


class Server(_Server):
    help = description = 'Runs the web server'

    def __call__(self, app, **kwargs):
        app.run(host='0.0.0.0')

manager.add_command("runserver", Server())


@manager.command
def createdb():
    """Creates the database."""
    if prompt_bool("Are you sure you want to reset the DB?"):
        db.drop_all()
        db.create_all()

if __name__ == '__main__':
    manager.run()