import json
from json.decoder import JSONDecodeError

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import async_to_sync


class ArenaConsumer(AsyncJsonWebsocketConsumer): 

    async def connect(self) -> None:
     
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chess_{self.room_id}"

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )

        await self.accept()


    async def disconnect(self, code):
        await super().disconnect(code)

    
    async def echo_message(self, message): 
        await self.send_json({
            "type": message.get("type"),
            "data": message.get("data")
        })

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type")
        if message_type == "echo.message":
            await self.send_json({
                "type": message_type,
                "data": content.get("data")
            })






