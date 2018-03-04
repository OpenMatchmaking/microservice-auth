from sanic import Blueprint

from app.token.api.views import generate_tokens, verify_token, refresh_token_pairs


token_bp = Blueprint('json-web-token-api', url_prefix='auth/api/token')
token_bp.add_route(generate_tokens, '/new', methods=['POST', ], name='create-token')
token_bp.add_route(verify_token, '/verify', methods=['POST', ], name='verify-token')
token_bp.add_route(refresh_token_pairs, '/refresh', methods=['POST', ], name='refresh-token')
