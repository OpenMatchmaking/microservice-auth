from pymongo import TEXT, DeleteOne, ReplaceOne
from pymongo.collation import Collation
from umongo import Document
from umongo.fields import StringField, ListField, ReferenceField

from app import app
from app.permissions.documents import Permission


instance = app.config["LAZY_UMONGO"]


@instance.register
class Group(Document):
    name = StringField(allow_none=False, required=True)
    permissions = ListField(ReferenceField(Permission))

    @classmethod
    async def synchronize_permissions(cls, old_permissions_ids, new_permissions_ids):
        deleted_permissions = list(set(old_permissions_ids) - set(new_permissions_ids))
        if deleted_permissions:
            await Group.collection.update_many(
                {},
                {"$pull": {"permissions": {"$in": deleted_permissions}}}
            )

        new_permissions = list(set(new_permissions_ids) - set(old_permissions_ids))
        if not new_permissions_ids:
            return

        for group_name, config in app.config["DEFAULT_GROUPS"].items():
            inserted_permissions = new_permissions[:]
            filter_expression = config.get('filter', None)
            if filter_expression:
                pipeline = [
                    {"$match": {
                        "$and": [
                            {"_id": {"$in": inserted_permissions}},
                            filter_expression
                        ]
                    }},
                    {'$group': {'_id': None, 'ids': {'$addToSet': '$_id'}}}
                ]
                query_result = await Permission.collection.aggregate(pipeline).to_list(1)
                inserted_permissions = query_result[0]['ids'] if query_result else []

            if inserted_permissions:
                await Group.collection.update_many(
                    {"name": group_name},
                    {"$addToSet": {"permissions": {"$each": inserted_permissions}}}
                )

    class Meta:
        indexes = {
            "keys": [('name', TEXT), ],
            "collation": Collation(locale="en", strength=2)
        }
