from sanic_script import Manager

from app import app
from app.commands.prepare_mongodb import PrepareMongoDbCommand
from app.commands.run_tests import RunTestsCommand
from app.commands.run_server import RunServerCommand


manager = Manager(app)
manager.add_command('run', RunServerCommand)
manager.add_command('prepare_mongodb', PrepareMongoDbCommand)
manager.add_command('test', RunTestsCommand)


if __name__ == '__main__':
    manager.run()
