import graphene
import graphql_jwt
from chat.schema import Query as ChatQuery, Mutation as ChatMutation, Subscription as ChatSubscription

class Query(ChatQuery, graphene.ObjectType):
    pass

class Mutation(ChatMutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

class Subscription(ChatSubscription, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)