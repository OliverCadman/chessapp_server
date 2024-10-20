from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import Player, Room
from common.tests.utils import create_test_datetime


class PlayerModelTests(TestCase):

    
    """
    - Creation of Player Model with Authenticated User
    - Creation of Player Model with AnonymousUser
    - TODO: Deletion of Player Model
    - TODO: Update 'last seen' status of Player
    """

    def test_create_player(self):
        """
        Test successful creation of Player DB instance
        """

        auth_user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpass123!"
        )

        room_name = "test_room"
        room, _ = Room.objects.get_or_create(
            room_name=room_name
        )

        last_seen = create_test_datetime()
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

    def test_create_player_unauthenticated_user(self):
        """
        Test creating a player with unauthenticated user successful.
        """

        last_seen = create_test_datetime()

        room_name="test_room"
        room, _ = Room.objects.get_or_create(
            room_name=room_name
        )

        last_seen = create_test_datetime()

        Player.objects.create(
            auth_user=None,
            room_name=room_name,
            room=room,
            last_seen=last_seen
        )

        players = Player.objects.all()
        self.assertEqual(len(players), 1)

        player_user_prop = players[0].auth_user
        player_room_prop = players[0].room
        player_lastseen_prop = players[0].last_seen

        self.assertEqual(player_user_prop, None)
        self.assertEqual(player_room_prop, room)
        self.assertEqual(player_lastseen_prop, last_seen)

