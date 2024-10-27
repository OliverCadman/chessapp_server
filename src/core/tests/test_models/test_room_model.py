from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Room, Player
from common.tests.utils import create_user
from core.exceptions import RoomFullException


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

    def test_is_full_returns_false_when_three_players_in_room(self):
        """
        Test that the _is_full method of the Room object
        returns False when a given Room contains more than two players.
        """
        
        room_name = "test_room"

        room = Room.objects.create(room_name=room_name)

        test_user_1 = create_user()
        test_user_2 = create_user(email="another@example.com")
        test_user_3 = create_user(email="third@example.com")

        player_channel_name_1 = "player_channel_1"
        room.add_player(
            user=test_user_1,
            channel_name=player_channel_name_1
        )

        player_channel_name_2 = "player_channel_2"
        room.add_player(
            user=test_user_2,
            channel_name=player_channel_name_2
        )

        # Should not raise this error.
        try:
            player_channel_name_3 = "player_channel_3"
            room.add_player(
                user=test_user_3,
                channel_name=player_channel_name_3
            )
        except RoomFullException as e:
            self.fail(e)
    
        room_with_size_test = Room.objects.get(id=room.id)
        self.assertEqual(len(room_with_size_test.player_set.all()), 3)

    def test_is_empty_returns_true_when_final_player_deleted(self):
        """
        Test that the _is_empty method of Room object
        returns True when no Players in a given room.
        """
        room_name = "test_room"

        room = Room.objects.create(room_name=room_name)

        test_user_1 = create_user()
        test_user_2 = create_user(email="another@example.com")

        player_channel_name_1 = "player_channel_1"
        room.add_player(
            user=test_user_1,
            channel_name=player_channel_name_1
        )

        player_channel_name_2 = "player_channel_2"
        room.add_player(
            user=test_user_2,
            channel_name=player_channel_name_2
        )


        Player.objects.all().delete()

        assert room.is_empty == True

    def test_is_empty_returns_false_when_players_associated(self):
        """
        Test that the _is_empty method returns false if there are
        Players in a given room
        """

        room_name = "test_room"

        room = Room.objects.create(room_name=room_name)

        test_user_1 = create_user()
        test_user_2 = create_user(email="another@example.com")


        player_channel_name_1 = "player_channel_1"
        room.add_player(
            user=test_user_1,
            channel_name=player_channel_name_1
        )

        player_channel_name_2 = "player_channel_2"
        room.add_player(
            user=test_user_2,
            channel_name=player_channel_name_2
        )

        Player.objects.filter(auth_user=test_user_1).delete()

        assert room.is_empty == False

    def test_add_player(self):
        """
        Test adding player to Room after room creation
        """

        room_name = "test_room"

        room = Room.objects.create(room_name=room_name)

        auth_user = create_user()

        player_channel_name_1 = "player_channel_1"
        player = room.add_player(
            user=auth_user,
            channel_name=player_channel_name_1
        )

        players = Player.objects.all()
        self.assertEqual(len(players), 1)

        self.assertEqual(player.auth_user, auth_user)
        self.assertEqual(player.room, room)
        self.assertEqual(player.channel_name, player_channel_name_1)


class RoomModelIntegrationTests(TestCase):
    """
    Tests to confirm that at the point an authenticated user
    creates a Room (by opening a websocket connection), they 
    are added to that room as a player.
    """

    def test_add_room_with_auth_user(self):

        room_name = "test_room"

        auth_user = create_user()

        player_channel_name = "player_channel_1"
        Room.objects.add_room(room_name, player_channel_name, auth_user)

        rooms = Room.objects.all()
        players = Player.objects.all()

        users = get_user_model().objects.all()

        self.assertEqual(len(rooms), 1)
        self.assertEqual(len(players), 1)

        self.assertEqual(rooms[0].room_name, room_name)
        self.assertEqual(players[0].auth_user, auth_user)
        self.assertEqual(players[0].channel_name, player_channel_name)
        self.assertEqual(players[0].room, rooms[0])
        