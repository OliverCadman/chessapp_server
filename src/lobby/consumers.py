from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from core.models import Room, Player
from core.exceptions import MessageNotSupportedException, RoomNotFoundException
from core.serializers import RoomSerializer

from lobby.channels import send_message_to_user_group


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
    def _add_room(self, room_name, channel_name):
        Room.objects.add_room(
                room_name=room_name,
                user_channel_name=channel_name,
                user=self.user
            )
            
    @database_sync_to_async
    def _get_user(self, user_id):
        return get_user_model().objects.get(id=user_id)
    
    @database_sync_to_async
    def _leave_rooms(self, channel_name):
        Player.objects.leave_rooms(channel_name=channel_name)

    async def connect(self):
        
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.user_group_name = f"user_{self.user.id}"
        
        if self.user.is_anonymous:
            await self.close()
        else:
            self.room_name = f"room_{self.room_id}"
            await self._add_room(
                self.room_name,
                self.channel_name
            )

            await self.channel_layer.group_add(
                self.room_name, self.channel_name
            )

            await self.channel_layer.group_add(
                self.user_group_name, self.channel_name
            )
            await self.accept()
    
    async def disconnect(self, code):
        room_id = self.scope["url_route"]["kwargs"]["room_id"]
        room_group_name = f"room_{room_id}"

        await self._leave_rooms(self.channel_name)
        await self.channel_layer.group_discard(
            room_group_name, self.channel_name
        )

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type")

        supported_message_types = [
            "lobby.challenge",
            "challenge.change.request",
            "player.list"
        ]

        if message_type in supported_message_types:
            data = content.get("data")
            group_name = content.get("group_name")

            await send_message_to_user_group(group_name, content)
            await self.send_json({
                "group_name": group_name,
                "type": message_type,
                "data": data
            })
        else:
            raise MessageNotSupportedException(
                f"Message of type '{message_type}' not supported.", 
            )

    async def lobby_challenge(self, message):
        message_type = message.get("type")
        data = message.get("data")
        await self.send_json(
                {
                    "type": message_type,
                    "data": data
                }
            )

    async def challenge_change_request(self, message):
        await self.send_json({
            "type": message.get("type"),
            "data": message.get("data")
        })

    @database_sync_to_async
    def _get_player_list(self, room_name, current_user_email):
        print("ROOMS:", Room.objects.all())

        try:
            room = Room.objects.get(room_name=room_name)
            serializer = RoomSerializer(room, current_user_email=current_user_email)
            data = serializer.data

            return data
        except Room.DoesNotExist:
            raise RoomNotFoundException(f"Room with name {room_name} could not be found.")

    async def player_list(self, message):
        room_name = message.get("group_name")
        current_user_email = message.get("data")["current_user_email"]

        print("MSG:", message)
        
        try:
            data = await self._get_player_list(room_name, current_user_email)
            await self.send_json({
                "type": message.get("type"),
                "data": data
            })
        except RoomNotFoundException as e:
            await self.send_json({
                "type": message.get("type"),
                "data": e.msg
            })

            self.close()
