from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from lobby.exceptions import RoomFullException, RoomNotFoundException

import os




class RoomManager(models.Manager):
    """
    Extend base manager with custom query methods
    """

    def remove_player_from_room(self, user):
        try:
            room = self.get_room_by_user(user)
            room.player_set.remove(user)

            if room._is_empty:
                room.delete()

        except RoomNotFoundException as err:
            raise err
    

    def get_room_by_user(self, user):
        try:
            room = Room.objects.get(player__auth_user=user)
            return room
        except Room.DoesNotExist:
            raise RoomNotFoundException(
                msg=f"Room for user '{user}' not found"
            )

    def add_room(self, room_name: str, user: User = None):
        """
        Creates a new Room object upon socket connection, 
        and assigns the Room to the Player (user) who opened the socket.
        """

        room, _ = Room.objects.get_or_create(
            room_name=room_name
        )

        try:
            room.add_player(
                room_name=room_name,
                user=user
            )
        except RoomFullException as err:
            raise err

        return room

class Room(models.Model):
    """
    Represents a channel room.
    """

    class Meta:
        db_table = "room"

    objects = RoomManager()

    room_name = models.CharField(
        max_length=255, unique=True, help_text="Unique identifier for a room."
    )

    def __str__(self):
        return self.room_name

    def add_player(self, room_name, user):
        """
        Create an instance of a Player object, assigning the current instance
        of Room as the foreign key.

        If room already contains two players, raise exception to be caught by function caller.
        """

        if self._is_full:
            raise RoomFullException(
                f"Room \"{self.room_name}\" cannot accept more than two players."
            )

        player, _ = Player.objects.get_or_create(
            auth_user=user,
            room=self,
            room_name=room_name,
            last_seen=timezone.now()
        )

        return player
    
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

    @property
    def is_empty(self):
        """
        Return true if room is empty, as a result of the only player left in the room
        leaving.
        """

        users_in_room = get_user_model().objects.filter(
            player__room=self
        )

        return len(users_in_room) == 0

class Player(models.Model):
    """
    Reperesents a Player
    """

    class Meta:
        db_table = "player"

    auth_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    room = models.ForeignKey("Room", on_delete=models.CASCADE)
    room_name = models.CharField(max_length=255, help_text="Room name for connected player")
    last_seen = models.DateTimeField(default=timezone.now())

    def __str__(self):
        return self.auth_user.email
