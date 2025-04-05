import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from graphene_subscriptions.events import CREATED
from .models import Conversation, Message
from users.models import User

# Types
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'name', 'email')

class ConversationType(DjangoObjectType):
    class Meta:
        model = Conversation
        fields = '__all__'

class MessageType(DjangoObjectType):
    class Meta:
        model = Message
        fields = '__all__'

# Queries
class Query(graphene.ObjectType):
    conversations = graphene.List(ConversationType)
    conversation = graphene.Field(ConversationType, id=graphene.ID(required=True))
    messages = graphene.List(MessageType, conversation_id=graphene.ID(required=True))
    
    @login_required
    def resolve_conversations(self, info):
        user = info.context.user
        return Conversation.objects.filter(participants=user)
    
    @login_required
    def resolve_conversation(self, info, id):
        user = info.context.user
        return Conversation.objects.filter(id=id, participants=user).first()
    
    @login_required
    def resolve_messages(self, info, conversation_id):
        user = info.context.user
        conversation = Conversation.objects.filter(id=conversation_id, participants=user).first()
        if conversation:
            return Message.objects.filter(conversation=conversation)
        return []

# Mutations
class CreateConversation(graphene.Mutation):
    class Arguments:
        participant_ids = graphene.List(graphene.ID, required=True)
    
    conversation = graphene.Field(ConversationType)
    
    @login_required
    def mutate(self, info, participant_ids):
        user = info.context.user
        participant_ids.append(str(user.id)) 
        
        participant_ids = list(set([int(id) for id in participant_ids]))
        
        conversation = Conversation.objects.create()
        participants = User.objects.filter(id__in=participant_ids)
        conversation.participants.set(participants)
        
        return CreateConversation(conversation=conversation)

class SendMessage(graphene.Mutation):
    class Arguments:
        conversation_id = graphene.ID(required=True)
        content = graphene.String(required=True)
    
    message = graphene.Field(MessageType)
    
    @login_required
    def mutate(self, info, conversation_id, content):
        user = info.context.user
        
        conversation = Conversation.objects.filter(
            id=conversation_id, 
            participants=user
        ).first()
        
        if not conversation:
            raise Exception("Conversation not found or you're not a participant")
            
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=content
        )
        
        conversation.save()
        
        return SendMessage(message=message)

class Mutation(graphene.ObjectType):
    create_conversation = CreateConversation.Field()
    send_message = SendMessage.Field()

# Subscriptions
class MessageSent(graphene.ObjectType):
    message = graphene.Field(MessageType)

class Subscription(graphene.ObjectType):
    message_sent = graphene.Field(MessageType, conversation_id=graphene.ID())
    
    def resolve_message_sent(root, info, conversation_id):
        return root.filter(
            lambda event:
                event.operation == CREATED and
                isinstance(event.instance, Message) and
                str(event.instance.conversation.id) == conversation_id and
                event.instance.conversation.participants.filter(id=info.context.user.id).exists()
        ).map(lambda event: event.instance)