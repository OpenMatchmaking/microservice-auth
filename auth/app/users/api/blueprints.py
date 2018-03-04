from sanic import Blueprint

from app.users.api.v1.views import RegisterGameClientView, UserProfileView


users_bp_v1 = Blueprint('users', url_prefix='auth/api/v1')
users_bp_v1.add_route(
    RegisterGameClientView.as_view(),
    '/users/game-client/register',
    name='game-client-register'
)
users_bp_v1.add_route(UserProfileView.as_view(), '/users/me', name='profile')
