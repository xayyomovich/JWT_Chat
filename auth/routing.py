from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from graphene_subscriptions.consumers import GraphqlSubscriptionConsumer
from chat.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "websocket": JWTAuthMiddleware(
        URLRouter([
            path("graphql/", GraphqlSubscriptionConsumer()),
        ])
    ),
})