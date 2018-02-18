from sanic.response import json
from sanic.views import HTTPMethodView

from marshmallow import ValidationError


class APIView(HTTPMethodView):
    """
    Generic API view for writing CRUD.
    """
    document = None
    schema = None

    def __init__(self):
        super(APIView, self).__init__()
        # For avoiding any import issues when using Sanic app necessary to
        # specify all required dependencies (that imports the main `app`
        # itself) and re-assign it to the variables inside the class

    def deserialize(self, data):
        result = self.schema().load(data or {})
        if result.errors:
            raise ValidationError(result.errors)
        return result.data

    def serialize(self, obj, **kwargs):
        serializer = self.schema(**kwargs)
        result = serializer.dump(obj)
        if result.errors:
            raise ValidationError(result.errors)
        return result.data
