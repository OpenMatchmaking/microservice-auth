from marshmallow import UnmarshalResult

from app import app


Microservice = app.config["LAZY_UMONGO"].Microservice
Permission = app.config["LAZY_UMONGO"].Permission


class MicroserviceSchema(Microservice.schema.as_marshmallow_schema()):

    def validate_permissions(self, data, errors_result):
        permissions = Permission.Schema(many=True).load(data)
        if permissions.errors:
            errors_result.update({'permissions': permissions.errors})

    def load(self, data, *args, **kwargs):
        permissions_data = data.pop('permissions', [])

        errors = {}
        result = super(MicroserviceSchema, self).load(data, *args, **kwargs)
        errors.update(result.errors)
        self.validate_permissions(permissions_data, errors)
        if errors:
            return UnmarshalResult(data=None, errors=errors)

        # self.load_permissions(permissions_data, result.data)
        return result
