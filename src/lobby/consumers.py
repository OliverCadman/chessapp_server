from lobby.models import Room, Player
from lobby.exceptions import (
    RoomFullException, 
    PlayerNotFoundException, 
    RoomNotFoundException
)

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist


class ArenaConsumer(AsyncJsonWebsocketConsumer): 
    @database_sync_to_async
    def _add_room(self, room_name):
        try:
            Room.objects.add_room(
                    room_name=room_name,
                    user=self.user
                )
        except RoomFullException as err:
            raise err
        
    @database_sync_to_async
    def _get_room_by_auth_user(self, user):
        try:
            room = Room.objects.get(player__auth_user=user)
            return room
        except Room.DoesNotExist:
            raise RoomNotFoundException(
                msg=f"Room for user '{user}' not found"
            )

    @database_sync_to_async
    def _delete_player(self, user):
        try:
            player = Player.objects.get(auth_user=user.id)
            room = Room.objects.get(player=player.id)
        except (Player.DoesNotExist, Room.DoesNotExist):
            return

        # If the deleted player is the final player in the room
        if len(room.player_set.all()) <= 1:
            room.delete()
        player.delete()


    async def connect(self) -> None:
        """
        Check if user is authorized, then add to group.
        If user is unauthorized, close the socket.
        """

        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chess_{self.room_id}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
        else:
            try:
                await self._add_room(self.room_group_name)
                print("SUCCESS")
            except RoomFullException:
                print("ROOM FULL! ERROR RAISED.")
                await self.close(
                    code=403,
                    reason="Room full"
                )

            await self.channel_layer.group_add(
                self.room_group_name, self.channel_name
            )

            await self.accept()


    async def disconnect(self, code):
        try: 
            user = self.scope["user"]
            await self._delete_player(user)
            
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

        except KeyError:
            return code
        except RoomNotFoundException as err:
            print(err)
            return code

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






