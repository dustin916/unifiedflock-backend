from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token

@database_sync_to_async
def get_user(token_key):
    try:
        return Token.objects.get(key=token_key).user
    except Token.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner
    
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        query_params = dict(qp.split('=') for qp in query_string.split('&') if '=' in qp)
        token_key = query_params.get('token')

        if token_key:
            scope['user'] = await get_user(token_key)
        else:
            scope['user'] = AnonymousUser()
        
        return await self.inner(scope, receive, send)