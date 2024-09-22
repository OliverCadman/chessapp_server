from channels.generic.websocket import AsyncJsonWebsocketConsumer
from arena.models import Room
from arena.exceptions import RoomFullException
from channels.db import database_sync_to_async




class ArenaConsumer(AsyncJsonWebsocketConsumer): 


    @database_sync_to_async
    def _get_or_create_room(self, room_name):
        try:
            print("hello")
            Room.objects.add_room(
                    channel_name=room_name,
                    user=self.user
                )
        except RoomFullException:
            raise RoomFullException

    async def connect(self) -> None:
        """
        Check if user is authorized, then add to group.
        If user is unauthorized, close the socket.


        """

      

        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
        else:
            self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
            self.room_group_name = f"chess_{self.room_id}"

            try:
                await self._get_or_create_room(self.room_group_name)
            except RoomFullException:
                print("FAIL")
                await self.close()

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






