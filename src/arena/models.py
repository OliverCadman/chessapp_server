from django.db import models
from django.conf import settings
from django.utils import timezone

class Room(models.Model):
    """
    Represents a channel room.
    """

    channel_name = models.CharField(
        max_length=255, unique=True, help_text="Unique identifier for a channel room."
    )

    def __str__(self):
        return self.channel_name
    
    def do(self):
        print(f"SELF: {self}")


class Player(models.Model):
    """
    Reperesents a Player
    """

    auth_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey("Room", on_delete=models.CASCADE)
    channel_name = models.CharField(max_length=255, help_text="Channel for connected player")
    last_seen = models.DateTimeField(default=timezone.now())
