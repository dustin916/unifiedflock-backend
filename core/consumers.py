import json
import redis
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from datetime import datetime
from .models import ChatMessage, Church

r = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

User = get_user_model()
class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.church_id = self.scope['url_route']['kwargs']['church_id']
        self.user = self.scope.get('user')

        self.room_group_name = f'chat_{self.church_id}'

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        r.sadd(f'online_users_{self.church_id}', self.user.id)

        # Join chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.broadcast_user_list()

    async def disconnect(self, close_code):
        # Leave chat
        if hasattr(self, 'room_group_name'):
            r.srem(f'online_users_{self.church_id}', self.user.id)
            await self.broadcast_user_list()

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
    async def broadcast_user_list(self):
        user_ids = [int(id) for id in r.smembers(f'online_users_{self.church_id}')]
        users_data = await self.get_user_details(user_ids)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_list',
                'users': users_data
            }
        )
    
    @database_sync_to_async
    def get_user_details (self, user_ids):
        users = User.objects.filter(id__in=user_ids)
        return [{'id': u.id, 'full_name': u.get_full_name() or u.username} for u in users]
    
    async def user_list(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_list',
            'users': event['users']
        }))

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope["user"]


        if data.get("type") == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_event",
                    "full_name": user.get_full_name() or user.username,
                    "user_id": user.id
                }
            )
            return

        message = data.get("message")

        if message:
            full_name = user.get_full_name() or user.username

            # Save message
            saved_msg = await self.save_message(user, self.church_id, message)

            # Send to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "full_name": full_name,
                    "timestamp": saved_msg.created.strftime("%b %d, %H:%M"),
                    "user_id": user.id,  
                    "message_id": saved_msg.id,
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat",
            "message": event["message"],
            "full_name": event["full_name"],
            "timestamp": event["timestamp"],
            "user_id": event["user_id"],
            "message_id": event["message_id"]
        }))

    async def typing_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "full_name": event["full_name"],
            "user_id": event["user_id"]
        }))

    # Save to database
    
    @database_sync_to_async
    def save_message(self, user, church_id, message):
        church = Church.objects.get(id=church_id)

        return ChatMessage.objects.create(
            user=user,
            church=church,
            message=message
        )