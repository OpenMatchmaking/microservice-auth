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

    def clean_collections(self):
        print("Clearing collections...")
        User.ensure_indexes()
        print("User document was initialized...")

        Group.ensure_indexes()
        print("Group document was initialized...")

        Permission.ensure_indexes()
        print("Permission document was initialized...")

        Microservice.ensure_indexes()
        print("Microservice document was initialized...")
        print("Done!")

    async def create_default_groups(self):
        print("Creating default empty groups...")
        for group_name, config in self.app.config['DEFAULT_GROUPS'].items():
            data = {'name': group_name}
            obj = await Group.collection.find_one(data)
            if not obj:
                data.update(config.get('init', {}))
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
