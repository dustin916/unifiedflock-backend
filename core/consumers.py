import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from datetime import datetime
from .models import ChatMessage, Church

User = get_user_model()
class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.church_id = self.scope['url_route']['kwargs']['church_id']
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        self.room_group_name = f'chat_{self.church_id}'
        
        # Join chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave chat
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope["user"]


        if data.get("type") == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_event",
                    "full_name": user.get_full_name() or user.username
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
            "full_name": event["full_name"]
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