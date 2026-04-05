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
        self.room_group_name = f'chat_{self.church_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope["user"]

        # -------------------------
        # TYPING EVENT
        # -------------------------
        if data.get("type") == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_event",
                    "full_name": user.get_full_name() or user.username
                }
            )
            return

        # -------------------------
        # CHAT MESSAGE
        # -------------------------
        message = data.get("message")

        if message:
            full_name = user.get_full_name() or user.username

            # Save message
            await self.save_message(user, self.church_id, message)

            # Send to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "full_name": full_name,
                    "timestamp": datetime.now().strftime("%b %d, %H:%M"),
                    "user_id": user.id,   # ✅ REQUIRED
                }
            )

    # -------------------------
    # RECEIVE CHAT MESSAGE
    # -------------------------
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat",
            "message": event["message"],
            "full_name": event["full_name"],
            "timestamp": event["timestamp"],
            "user_id": event["user_id"]
        }))

    # -------------------------
    # RECEIVE TYPING EVENT
    # -------------------------
    async def typing_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "full_name": event["full_name"]
        }))

    # -------------------------
    # DB SAVE (SYNC WRAPPER)
    # -------------------------
    @database_sync_to_async
    def save_message(self, user, church_id, message):
        church = Church.objects.get(id=church_id)

        return ChatMessage.objects.create(
            user=user,
            church=church,
            message=message
        )