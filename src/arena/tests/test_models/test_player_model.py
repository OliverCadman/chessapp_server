from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from arena.models import Player, Room
from datetime import timezone as tz

class PlayerModelTests(TestCase):

    
    """
    - Creation of Player Model with Authenticated User
    - Creation of Player Model with AnonymousUser
    - Deletion of Player Model
    - Update 'last seen' status of Player
    """

    def test_create_player(self):
        """
        Test successful creation of Player DB instance
        """

        auth_user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpass123!"
        )

        channel_name = "test_channel"
        room, _ = Room.objects.get_or_create(
            channel_name=channel_name
        )

        last_seen = timezone.datetime(2024, 9, 15, tzinfo=tz.utc)
        Player.objects.get_or_create(
            auth_user=auth_user,
            room=room,
            last_seen=last_seen
        )

        players = Player.objects.all()
        self.assertEqual(len(players), 1)

        player_user_prop = players[0].auth_user
        player_room_prop = players[0].room
        player_lastseen_prop = players[0].last_seen

        self.assertEqual(player_user_prop, auth_user)
        self.assertEqual(player_room_prop, room)
        self.assertEqual(player_lastseen_prop, last_seen)