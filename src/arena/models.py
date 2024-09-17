from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from arena.exceptions import RoomFullException

import os


class RoomManager(models.Manager):
    """
    Extend base manager with custom query methods
    """

    def add_room(self, channel_name: str, user: User = None):
        """
        Creates a new Room object upon socket connection, 
        and assigns the Room to the Player (user) who opened the socket.
        """

        room, _ = Room.objects.get_or_create(
            channel_name=channel_name
        )

        room.add_player(
            channel_name=channel_name,
            user=user
        )

        return room


class Room(models.Model):
    """
    Represents a channel room.
    """

    objects = RoomManager()

    channel_name = models.CharField(
        max_length=255, unique=True, help_text="Unique identifier for a channel room."
    )

    def __str__(self):
        return self.channel_name
    
    def add_player(self, channel_name, user):
        """
        Create an instance of a Player object, assigning the current instance
        of Room as the foreign key.

        If room already contains two players, raise exception to be caught by function caller.
        """

        if self.is_full:
            raise RoomFullException(
                f"Room \"{self.channel_name}\" cannot accept more than two players."
            )

        player, _ = Player.objects.get_or_create(
            auth_user=user,
            room=self,
            channel_name=channel_name,
            last_seen=timezone.now()
        )

        return player
    
    @property
    def is_full(self):
        """
        Return true if two or more Player instances have this same Room instance
        assigned to them.
        """

        users_in_room = get_user_model().objects.filter(
            player__room=self
            )
        
        return len(users_in_room) >= int(os.environ.get("ROOM_SIZE_THRESHOLD"))
        

class Player(models.Model):
    """
    Reperesents a Player
    """

    auth_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    room = models.ForeignKey("Room", on_delete=models.CASCADE)
    channel_name = models.CharField(max_length=255, help_text="Channel for connected player")
    last_seen = models.DateTimeField(default=timezone.now())
