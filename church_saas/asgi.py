import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from core.middleware import TokenAuthMiddleware
import core.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_saas.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        TokenAuthMiddleware(
            URLRouter(
                core.routing.websocket_urlpatterns
            )
        )
    ),
})