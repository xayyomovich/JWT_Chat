from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.db import close_old_connections
import jwt
from django.conf import settings
from users.models import User

@database_sync_to_async
def get_user(token_key):
    try:
        payload = jwt.decode(token_key, 'secret', algorithms=['HS256'])
        user = User.objects.get(id=payload['id'])
        return user
    except (jwt.DecodeError, User.DoesNotExist):
        return None

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        close_old_connections()
        
        # Get the token from query string
        query_string = scope.get('query_string', b'').decode()
        token = None
        
        # Simple parsing of query string for token
        params = query_string.split('&')
        for param in params:
            if param.startswith('token='):
                token = param.split('=')[1]
                break
        
        if token:
            user = await get_user(token)
            if user:
                scope['user'] = user
        
        return await super().__call__(scope, receive, send)