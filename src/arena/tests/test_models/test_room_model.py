from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Player
from arena.models import ArenaRoom
from common.tests.utils import create_user
from core.exceptions import RoomFullException


class RoomModelUnitTests(TestCase):
    """
    - Creation of Room
    - Deletion of room
    - Adding Player to Room

    """

    def test_is_full_returns_true_when_two_players_associated(self):
        """
        Test that the _is_full method of the Room object
        returns True when a given Room contains two Player objects.
        """

        
        room_name = "test_room"

        room = ArenaRoom.objects.create(room_name=room_name)

        test_user_1 = create_user()
        test_user_2 = create_user(email="another@example.com")

        player_channel_name_1 = "player_channel_1"
        room.add_player(
            user=test_user_1,
            channel_name=player_channel_name_1,
        )

        player_channel_name_2 = "player_channel_2"
        room.add_player(
            user=test_user_2,
            channel_name=player_channel_name_2,
        )

        assert room._is_full == True

    def test_is_full_returns_false_when_one_player_associated(self):
        """
        Test that the _is_full method of the Room object
        returns False if a given Room contains only one Player object.
        """
        
        room_name = "test_room"

        room = ArenaRoom.objects.create(room_name=room_name)

        test_user_1 = create_user()
    
        player_channel_name = "player_channel_1"
        room.add_player(
            user=test_user_1,
            channel_name=player_channel_name
        )

        assert room._is_full == False

    def test_adding_player_to_full_room_raises_exception(self):
        """
        Test if add_player method returns None if the room already contains 2 players.
        """

        first_auth_user = create_user()
        second_auth_user = create_user(email="another@example.com")

        room_name = "test_room"
        room = ArenaRoom.objects.create(room_name=room_name)

        # Add first player
        player_channel_name_1 = "player_channel_1"
        room.add_player(
            user=first_auth_user,
            channel_name=player_channel_name_1
        )

        # Add second player
        player_channel_name_2 = "player_channel_2"
        room.add_player(
            user=second_auth_user,
            channel_name=player_channel_name_2
        )

        with self.assertRaises(RoomFullException):
            # Add third player
            player_channel_name_3 = "player_channel_3"
            room.add_player(
                user=None,
                channel_name=player_channel_name_3
            )


class RoomModelIntegrationTests(TestCase):
    """
    Tests to confirm that at the point an authenticated user
    creates a Room (by opening a websocket connection), they 
    are added to that room as a player.
    """

    def test_add_room_with_auth_user(self):

        room_name = "test_room"

        auth_user = create_user()


        player_channel_name_1 = "player_channel_name"

        ArenaRoom.objects.add_room(room_name, player_channel_name_1, auth_user)

        rooms = ArenaRoom.objects.all()
        players = Player.objects.all()

        self.assertEqual(len(rooms), 1)
        self.assertEqual(len(players), 1)

        self.assertEqual(rooms[0].room_name, room_name)
        self.assertEqual(players[0].auth_user, auth_user)
        self.assertEqual(players[0].channel_name, player_channel_name_1)
        self.assertEqual(players[0].room, rooms[0])
        