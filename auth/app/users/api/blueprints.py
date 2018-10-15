from sanic import Blueprint

from app.users.api.v1.views import UserProfileView


users_bp_v1 = Blueprint('users', url_prefix='auth/api/v1')
users_bp_v1.add_route(UserProfileView.as_view(), '/users/me', name='profile')
