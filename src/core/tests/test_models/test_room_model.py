from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Room, Player
from common.tests.utils import create_test_datetime, create_user
from core.exceptions import RoomFullException

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

        room_name = "test_room"

        room = Room.objects.create(
            room_name=room_name
        )

        self.assertEqual(room.room_name, room_name)

        rooms = Room.objects.all()
        self.assertEqual(len(rooms), 1)

    def test_delete_room(self):
        """
        Test deletion of Channels room is successful.
        """

        room_name = "test_room"

        Room.objects.create(
            room_name=room_name
        )

        rooms = Room.objects.all()
        self.assertEqual(len(rooms), 1)

        room_to_delete = Room.objects.filter(room_name=room_name)
        room_to_delete.delete()

        rooms = Room.objects.all()
        self.assertEqual(len(rooms), 0)

    @patch("django.utils.timezone.now")
    def test_is_full_returns_false_when_three_players_in_room(self, patched_time):
        """
        Test that the _is_full method of the Room object
        returns False when a given Room contains more than two players.
        """

        patched_time.return_value = create_test_datetime()
        
        room_name = "test_room"

        room = Room.objects.create(room_name=room_name)

        test_user_1 = create_user()
        test_user_2 = create_user(email="another@example.com")
        test_user_3 = create_user(email="third@example.com")

        room.add_player(
            user=test_user_1,
            room_name=room_name
        )

        room.add_player(
            user=test_user_2,
            room_name=room_name
        )

        # Should not raise this error.
        try:
            room.add_player(
                user=test_user_3,
                room_name=room_name
            )
        except RoomFullException as e:
            self.fail(e)
    
        room_with_size_test = Room.objects.get(id=room.id)
        self.assertEqual(len(room_with_size_test.player_set.all()), 3)


    # @patch("django.utils.timezone.now")
    # def test_is_full_returns_false_when_one_player_associated(self, patched_time):
    #     """
    #     Test that the _is_full method of the Room object
    #     returns False if a given Room contains only one Player object.
    #     """
        
    #     room_name = "test_room"

    #     room = Room.objects.create(room_name=room_name)

    #     patched_time.return_value = create_test_datetime()

    #     test_user_1 = create_user()
    
    #     room.add_player(
    #         user=test_user_1,
    #         room_name=room_name
    #     )

    #     assert room._is_full == False

    @patch("django.utils.timezone.now")
    def test_is_empty_returns_true_when_final_player_deleted(self, patched_time):
        """
        Test that the _is_empty method of Room object
        returns True when no Players in a given room.
        """
        room_name = "test_room"

        room = Room.objects.create(room_name=room_name)

        patched_time.return_value = create_test_datetime()

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

        # TODO: room.remove_player
        Player.objects.all().delete()

        assert room.is_empty == True

    @patch("django.utils.timezone.now")
    def test_is_empty_returns_false_when_players_associated(self, patched_time):
        """
        Test that the _is_empty method returns false if there are
        Players in a given room
        """

        room_name = "test_room"

        room = Room.objects.create(room_name=room_name)

        test_user_1 = create_user()
        test_user_2 = create_user(email="another@example.com")

        patched_time.return_value = create_test_datetime()

        room.add_player(
            user=test_user_1,
            room_name=room_name
        )

        room.add_player(
            user=test_user_2,
            room_name=room_name
        )

        # TODO: room.remove_player
        Player.objects.filter(auth_user=test_user_1).delete()

        assert room.is_empty == False
        

    @patch("django.utils.timezone.now")
    def test_add_player(self, patched_time):
        """
        Test adding player to Room after room creation
        """

        patched_time.return_value = create_test_datetime()

        room_name = "test_room"

        room = Room.objects.create(room_name=room_name)

        auth_user = create_user()
        player = room.add_player(
            user=auth_user,
            room_name=room_name
        )

        players = Player.objects.all()
        self.assertEqual(len(players), 1)

        self.assertEqual(player.auth_user, auth_user)
        self.assertEqual(player.room, room)
        self.assertEqual(player.room_name, room_name)
        self.assertEqual(player.last_seen, patched_time.return_value)

    # @patch("django.utils.timezone")
    # def test_adding_player_to_full_room_raises_exception(self, patched_time):
    #     """
    #     Test if add_player method returns None if the room already contains 2 players.
    #     """

    #     patched_time.return_value = create_test_datetime()

    #     first_auth_user = create_user()
    #     second_auth_user = create_user(email="another@example.com")

    #     room_name = "test_room"
    #     room = Room.objects.create(room_name=room_name)

    #     # Add first player
    #     room.add_player(
    #         user=first_auth_user,
    #         room_name=room_name
    #     )

    #     # Add second player
    #     room.add_player(
    #         user=second_auth_user,
    #         room_name=room_name
    #     )

    #     with self.assertRaises(RoomFullException):
    #         # Add third player
    #         room.add_player(
    #             user=None,
    #             room_name=room_name
    #         )


class RoomModelIntegrationTests(TestCase):
    """
    Tests to confirm that at the point an authenticated user
    creates a Room (by opening a websocket connection), they 
    are added to that room as a player.
    """

    @patch("core.models.timezone.now")
    def test_add_room_with_auth_user(self, patched_time):

        patched_time.return_value = create_test_datetime()

        room_name = "test_room"

        auth_user = create_user()

        Room.objects.add_room(room_name, auth_user)

        rooms = Room.objects.all()
        players = Player.objects.all()

        users = get_user_model().objects.all()

        self.assertEqual(len(rooms), 1)
        self.assertEqual(len(players), 1)

        self.assertEqual(rooms[0].room_name, room_name)
        self.assertEqual(players[0].auth_user, auth_user)
        self.assertEqual(players[0].room_name, room_name)
        self.assertEqual(players[0].last_seen, patched_time.return_value)
        self.assertEqual(players[0].room, rooms[0])
        