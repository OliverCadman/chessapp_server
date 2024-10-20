from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

import uuid


class LobbyConsumer(AsyncJsonWebsocketConsumer):
    """
    Websocket event handler for chess arena lobby

    Events:
        - Player 1 submits game request to another player. Included data:
            - Time control
            - Colour
        
        - Player 2 accepts game request

        - Player 2 requests changes for either of the following:
            - Time control
            - Colour

            Player 1 accepts request

            Player 1 declines request

                Connection closes and game request needs to be re-submitted.

        - Player 2 declines request
    """


    @database_sync_to_async
    def _get_user(self, user_id):
        return get_user_model().objects.get(id=user_id)

    async def connect(self):
        
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
        else:
            self.user_group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.user_group_name, self.channel_name
            )
            await self.accept()
    
    async def receive_json(self, content, **kwargs):
        message_type = content.get("type")

        supported_message_types = [
            "lobby.challenge",
            "challenge.change.request"
        ]

        if message_type in supported_message_types:
            data = content.get("data")
            group_name = data["group_name"]

            await self.channel_layer.group_send(
                group_name, {
                    "type": message_type,
                    "data": data
                }
            )

    async def lobby_challenge(self, message):
        await self.send_json({
            "type": message.get("type"),
            "data": message.get("data")
        })

    async def challenge_change_request(self, message):
        await self.send_json({
            "type": message.get("type"),
            "data": message.get("data")
        })
