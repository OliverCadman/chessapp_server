from django.contrib.auth import get_user_model
from core.exceptions import RoomFullException
from core.models import RoomManager, Room

import os


class ArenaRoomManager(RoomManager):

    def add_room(self, room_name, channel_name, user):
        room, _ = ArenaRoom.objects.get_or_create(
            room_name=room_name
        )
        
        try:
            room.add_player(
                    channel_name=channel_name,
                    user=user
                )
        except RoomFullException as err:
            raise err
        
        return room


class ArenaRoom(Room):
    """
    Represents a channel room.
    """

    class Meta:
        db_table = "room"
        proxy = True

    objects = ArenaRoomManager()

    def add_player(self, channel_name, user):

        if self._is_full:
            raise RoomFullException(
                f"Room \"{self.room_name}\" cannot accept more than two players."
            )
        
        super().add_player(channel_name, user)

    @property
    def _is_full(self):
        """
        Return true if two or more Player instances have this same Room instance
        assigned to them.
        """

        users_in_room = get_user_model().objects.filter(
            player__room=self
            )
        
        return len(users_in_room) >= int(os.environ.get("ROOM_SIZE_THRESHOLD"))
