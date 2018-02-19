from sanic import Blueprint

from app.users.api.v1.users import RegisterGameClientView


users_bp_v1 = Blueprint('users', url_prefix='auth/api/v1')
users_bp_v1.add_route(
    RegisterGameClientView.as_view(),
    '/users/game-client/register',
    name='game-client-register'
)
