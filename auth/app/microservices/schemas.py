from marshmallow import UnmarshalResult
from pymongo import UpdateOne

from app import app


Microservice = app.config["LAZY_UMONGO"].Microservice
Permission = app.config["LAZY_UMONGO"].Permission


class MicroserviceSchema(Microservice.schema.as_marshmallow_schema()):

    def validate_permissions(self, data, errors_result):
        permissions = Permission.Schema(many=True).load(data)
        if permissions.errors:
            errors_result.update({'permissions': permissions.errors})

    async def load_permissions(self, data, result):
        requests = [
            UpdateOne({'codename': permission['codename']}, {'$set': permission}, upsert=True)
            for permission in data
        ]
        await Permission.collection.bulk_write(requests)

        pipeline = [
            {'$match': {'$or': [{'codename': permission['codename']} for permission in data]}},
            {'$group': {'_id': '_id', 'ids': {'$addToSet': '$_id'}}}
        ]
        permissions = await Permission.collection.aggregate(pipeline).to_list(1)
        result['permissions'] = permissions[0]['ids']

    def load(self, data, *args, **kwargs):
        permissions_data = data.pop('permissions', [])

        errors = {}
        result = super(MicroserviceSchema, self).load(data, *args, **kwargs)
        errors.update(result.errors)
        self.validate_permissions(permissions_data, errors)
        if errors:
            return UnmarshalResult(data=None, errors=errors)

        result.data['permissions'] = permissions_data
        return result
