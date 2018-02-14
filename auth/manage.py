from sanic_script import Manager

from app import app
from app.commands.runserver import RunServerCommand


manager = Manager(app)
manager.add_command('run', RunServerCommand)


if __name__ == '__main__':
    manager.run()
