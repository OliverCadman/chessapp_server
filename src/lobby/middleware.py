from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from django.core.exceptions import ObjectDoesNotExist
from channels.db import database_sync_to_async
from channels.sessions import CookieMiddleware, SessionMiddleware
from channels.auth import AuthMiddleware
from rest_framework_simplejwt.tokens import AccessToken


from urllib.parse import parse_qs


@database_sync_to_async
def get_user(scope):
    """
    
    """

    # Close any DB connections to avoid stale connections
    close_old_connections()
    query_string = parse_qs(scope["query_string"].decode())
    token = query_string.get("token")
    if not token:
        return AnonymousUser()
    
    try:
        access_token = AccessToken(token[0])
        user = get_user_model().objects.get(id=access_token["user_id"])
    except ObjectDoesNotExist:
        return AnonymousUser
    
    if not user.is_active:
        return AnonymousUser
    
    return user
    

class TokenMiddleware(AuthMiddleware):
    async def resolve_scope(self, scope):
        scope["user"]._wrapped = await get_user(scope)
    

def TokenMiddlewareStack(inner):
    return CookieMiddleware(SessionMiddleware(TokenMiddleware(inner)))
