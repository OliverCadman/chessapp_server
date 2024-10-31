from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from core.exceptions import RoomNotFoundException
from common.models.utils import current_datetime
from channels.db import database_sync_to_async

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, 
    PermissionsMixin,
    BaseUserManager
    )

from datetime import timedelta, datetime


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

    def add_room(self, room_name: str, user_channel_name: str, user: User = None):
        """
        Creates a new Room object upon socket connection, 
        and assigns the Room to the Player (user) who opened the socket.
        """

        room, _ = Room.objects.get_or_create(
            room_name=room_name
        )

        room.add_player(
            channel_name=user_channel_name,
            user=user
        )

        return room

    def prune_players(self, age=None):
        for room in Room.objects.all():
            room.prune_players(age)


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

    def add_player(self, channel_name, user):
        """
        Create an instance of a Player object, assigning the current instance
        of Room as the foreign key.

        If room already contains two players, raise exception to be caught by function caller.
        """

        player, _ = Player.objects.get_or_create(
            auth_user=user,
            room=self,
            channel_name=channel_name
        )

        return player

    def remove_player(self, channel_name, player=None):
        if not player:
            try:
                player = Player.objects.get(room=self, channel_name=channel_name)
            except Player.DoesNotExist:
                return

        player.delete()

    def prune_players(self, channel_name=None, age=None):

        if age is None:
            age = getattr(settings, "PLAYER_MAX_AGE", 60)

        print("'now()' in prune_players:", datetime.now())

        Player.objects.filter(
            room=self, 
            last_seen__lt=datetime.now() - timedelta(seconds=age)
            ).delete()

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

    @property
    def _is_full(self):
        pass


class PlayerManager(models.Manager):

    def touch(self, channel_name):
        self.filter(channel_name=channel_name).update(
            last_seen=current_datetime()
            )
        
    
    def leave_rooms(self, channel_name):
        for player in self.select_related("room").filter(channel_name=channel_name):
            room = player.room
            room.remove_player(channel_name)
    
    def get_or_create(self, *args, **kwargs):
        """
        Default implementation would create a new Player object
        if all Player details already exist, but only the channel name
        is different (which can might happen after a 
        player makes a subsequent connection to the websocket)
        """
        user = kwargs.pop("auth_user")
        try:
            return self.get(auth_user=user), False
        except Player.DoesNotExist:
            channel_name = kwargs.pop("channel_name")
            room = kwargs.pop("room")

            return self.create(
                channel_name=channel_name,
                auth_user=user,
                room=room
            ), True



class Player(models.Model):
    """
    Represents a Player
    """


    class Meta:
        db_table = "player"

    
    objects = PlayerManager()


    auth_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    room = models.ForeignKey("Room", on_delete=models.CASCADE)
    channel_name = models.CharField(max_length=255, help_text="Channel name for connected player")
    last_seen = models.DateTimeField(default=current_datetime())

    def __str__(self):
        return self.auth_user.email
    

class UserManager(BaseUserManager):
    """
    Custom manager for User model. Creates regular users and super users.
    """

    def create_user(self, email: str, password: str = None, **extra_fields):
        """Create a regular user."""

        if not email:
            raise ValueError("Please provide an email address.")
        
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user
    
    def create_superuser(self, email: str, password: str = None, **extra_fields):
        """Create superuser with staff and superuser status."""

        user = self.create_user(email, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self.db)

        return user


class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(max_length=244, unique=True, null=False)
    name = models.CharField(max_length=255)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"

    objects = UserManager()