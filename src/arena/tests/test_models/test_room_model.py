from django.test import TestCase
from django.contrib.auth import get_user_model
from arena.models import Room, Player
from arena.tests.utils.test_helpers import create_test_datetime, create_test_user
from arena.exceptions import RoomFullException

from unittest.mock import patch


class RoomModelUnitTests(TestCase):
    """
    - Creation of Room
    - Deletion of room
    - Adding Player to Room

    """

    def test_create_room(self):
        """
        Test creation of Channels room is successful.
        """

        channel_name = "test_channel"

        room = Room.objects.create(
            channel_name=channel_name
        )

        self.assertEqual(room.channel_name, channel_name)

        rooms = Room.objects.all()
        self.assertEqual(len(rooms), 1)

    def test_delete_room(self):
        """
        Test deletion of Channels room is successful.
        """

        channel_name = "test_channel"

        Room.objects.create(
            channel_name=channel_name
        )

        rooms = Room.objects.all()
        self.assertEqual(len(rooms), 1)

        room_to_delete = Room.objects.filter(channel_name=channel_name)
        room_to_delete.delete()

        rooms = Room.objects.all()
        self.assertEqual(len(rooms), 0)

    
    @patch("django.utils.timezone.now")
    def test_add_player(self, patched_time):
        """
        Test adding player to Room after room creation
        """

        patched_time.return_value = create_test_datetime()

        channel_name = "test_channel"

        room = Room.objects.create(channel_name=channel_name)

        auth_user = create_test_user()
        player = room.add_player(
            user=auth_user,
            channel_name=channel_name
        )

        players = Player.objects.all()
        self.assertEqual(len(players), 1)

        self.assertEqual(player.auth_user, auth_user)
        self.assertEqual(player.room, room)
        self.assertEqual(player.channel_name, channel_name)
        self.assertEqual(player.last_seen, patched_time.return_value)

    @patch("django.utils.timezone")
    def test_adding_player_to_full_room_returns_none(self, patched_time):
        """
        Test if add_player method returns None if the room already contains 2 players.
        """

        patched_time.return_value = create_test_datetime()

        first_auth_user = create_test_user()
        second_auth_user = create_test_user(email="another@example.com")

        channel_name = "test_channel"
        room = Room.objects.create(channel_name="test_channel")

        # Add first player
        room.add_player(
            user=first_auth_user,
            channel_name=channel_name
        )

        # Add second player
        room.add_player(
            user=second_auth_user,
            channel_name=channel_name
        )

        with self.assertRaises(RoomFullException):
            # Add third player
            room.add_player(
                user=None,
                channel_name=channel_name
            )


class RoomModelIntegrationTests(TestCase):

    @patch("arena.models.timezone.now")
    def test_add_room_with_auth_user(self, patched_time):

        patched_time.return_value = create_test_datetime()

        channel_name = "test_channel"

        auth_user = create_test_user()

        Room.objects.add_room(channel_name, auth_user)

        rooms = Room.objects.all()
        players = Player.objects.all()

        users = get_user_model().objects.all()

        self.assertEqual(len(rooms), 1)
        self.assertEqual(len(players), 1)

        self.assertEqual(rooms[0].channel_name, channel_name)
        self.assertEqual(players[0].auth_user, auth_user)
        self.assertEqual(players[0].channel_name, channel_name)
        self.assertEqual(players[0].last_seen, patched_time.return_value)
        self.assertEqual(players[0].room, rooms[0])
        