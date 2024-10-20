from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Player
from arena.models import ArenaRoom
from common.tests.utils import create_test_datetime, create_user
from core.exceptions import RoomFullException

from unittest.mock import patch


class RoomModelUnitTests(TestCase):
    """
    - Creation of Room
    - Deletion of room
    - Adding Player to Room

    """

    @patch("django.utils.timezone.now")
    def test_is_full_returns_true_when_two_players_associated(self, patched_time):
        """
        Test that the _is_full method of the Room object
        returns True when a given Room contains two Player objects.
        """

        patched_time.return_value = create_test_datetime()
        
        room_name = "test_room"

        room = ArenaRoom.objects.create(room_name=room_name)

        test_user_1 = create_user()
        test_user_2 = create_user(email="another@example.com")

        room.add_player(
            user=test_user_1,
            room_name=room_name
        )

        room.add_player(
            user=test_user_2,
            room_name=room_name
        )

        assert room._is_full == True

    @patch("django.utils.timezone.now")
    def test_is_full_returns_false_when_one_player_associated(self, patched_time):
        """
        Test that the _is_full method of the Room object
        returns False if a given Room contains only one Player object.
        """
        
        room_name = "test_room"

        room = ArenaRoom.objects.create(room_name=room_name)

        patched_time.return_value = create_test_datetime()

        test_user_1 = create_user()
    
        room.add_player(
            user=test_user_1,
            room_name=room_name
        )

        assert room._is_full == False

    @patch("django.utils.timezone")
    def test_adding_player_to_full_room_raises_exception(self, patched_time):
        """
        Test if add_player method returns None if the room already contains 2 players.
        """

        patched_time.return_value = create_test_datetime()

        first_auth_user = create_user()
        second_auth_user = create_user(email="another@example.com")

        room_name = "test_room"
        room = ArenaRoom.objects.create(room_name=room_name)

        # Add first player
        room.add_player(
            user=first_auth_user,
            room_name=room_name
        )

        # Add second player
        room.add_player(
            user=second_auth_user,
            room_name=room_name
        )

        with self.assertRaises(RoomFullException):
            # Add third player
            room.add_player(
                user=None,
                room_name=room_name
            )


class RoomModelIntegrationTests(TestCase):
    """
    Tests to confirm that at the point an authenticated user
    creates a Room (by opening a websocket connection), they 
    are added to that room as a player.
    """

    @patch("arena.models.timezone.now")
    def test_add_room_with_auth_user(self, patched_time):

        patched_time.return_value = create_test_datetime()

        room_name = "test_room"

        auth_user = create_user()

        ArenaRoom.objects.add_room(room_name, auth_user)

        rooms = ArenaRoom.objects.all()
        players = Player.objects.all()

        users = get_user_model().objects.all()

        self.assertEqual(len(rooms), 1)
        self.assertEqual(len(players), 1)

        self.assertEqual(rooms[0].room_name, room_name)
        self.assertEqual(players[0].auth_user, auth_user)
        self.assertEqual(players[0].room_name, room_name)
        self.assertEqual(players[0].last_seen, patched_time.return_value)
        self.assertEqual(players[0].room, rooms[0])
        