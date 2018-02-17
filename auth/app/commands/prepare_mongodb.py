from asyncio import get_event_loop

from motor.motor_asyncio import AsyncIOMotorClient
from sanic_script import Command

from app import app
from app.groups.documents import Group
from app.microservices.documents import Microservice
from app.permissions.documents import Permission
from app.users.documents import User


class PrepareMongoDbCommand(Command):
    """
    Clean up and fill the MongoDB with default data.
    """
    app = app
    default_groups = [
        {"name": "Game client", "permissions": []},
    ]

    def clean_collections(self):
        print("Clearing collections...")
        User.collection.drop()
        User.ensure_indexes()
        print("User document was initialized...")

        Group.collection.drop()
        Group.ensure_indexes()
        print("Group document was initialized...")

        Permission.collection.drop()
        Permission.ensure_indexes()
        print("Permission document was initialized...")

        Microservice.collection.drop()
        Microservice.ensure_indexes()
        print("Microservice document was initialized...")
        print("Done!")

    async def create_default_groups(self):
        print("Creating default empty groups...")
        for data in self.default_groups:
            Group.ensure_indexes()
            await Group(**data).commit()
        print('Creating has completed!')

    def prepare_db(self, loop):
        self.clean_collections()
        loop.run_until_complete(self.create_default_groups())

    def init_lazy_umongo(self):
        client = AsyncIOMotorClient(self.app.config['MONGODB_URI'])
        database = client[self.app.config['MONGODB_DATABASE']]
        lazy_umongo = self.app.config["LAZY_UMONGO"]
        lazy_umongo.init(database)

    def run(self, *args, **kwargs):
        self.init_lazy_umongo()
        loop = get_event_loop()
        self.prepare_db(loop)
