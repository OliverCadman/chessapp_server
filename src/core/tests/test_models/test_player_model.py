from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import Player, Room
from common.tests.utils import create_user

from unittest.mock import patch

from django.utils import timezone
from datetime import timezone as tz


class PlayerModelTests(TestCase):

    
    """
    - Creation of Player Model with Authenticated User
    - Creation of Player Model with AnonymousUser
    - TODO: Deletion of Player Model
    - TODO: Update 'last seen' status of Player
    """

    @patch("core.models.current_datetime")
    def test_create_player(self, patched_time):
        """
        Test successful creation of Player DB instance
        """

        test_timezone = timezone.datetime(2024, 9, 15, tzinfo=tz.utc)
        patched_time.return_value = test_timezone

        auth_user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpass123!"
        )

        room_name = "test_room"
        room, _ = Room.objects.get_or_create(
            room_name=room_name
        )

        channel_name = "player_channel"
        Player.objects.create(
            auth_user=auth_user,
            room=room,
            channel_name=channel_name,
            last_seen=test_timezone
        )

        players = Player.objects.all()
        self.assertEqual(len(players), 1)

        player_user_prop = players[0].auth_user
        player_room_prop = players[0].room
        player_lastseen_prop = players[0].last_seen

        self.assertEqual(player_user_prop, auth_user)
        self.assertEqual(player_room_prop, room)
        self.assertEqual(player_lastseen_prop, test_timezone)

    @patch("core.models.current_datetime")
    def test_create_player_unauthenticated_user(self, patched_time):
        """
        Test creating a player with unauthenticated user successful.
        """

        test_timezone = timezone.datetime(2024, 9, 15, tzinfo=tz.utc)
        patched_time.return_value = test_timezone

        channel_name="player_channel"
        room_name = "test_room"
        room, _ = Room.objects.get_or_create(
            room_name=room_name
        )

        Player.objects.create(
            auth_user=None,
            channel_name=channel_name,
            room=room,
            last_seen=test_timezone
        )

        players = Player.objects.all()
        self.assertEqual(len(players), 1)

        player_user_prop = players[0].auth_user
        player_room_prop = players[0].room
        player_lastseen_prop = players[0].last_seen


        self.assertEqual(player_user_prop, None)
        self.assertEqual(player_room_prop, room)
        self.assertEqual(player_lastseen_prop, test_timezone)

    @patch("core.models.current_datetime")
    def test_touch_updates_last_seen(self, patched_time):
        """
        Test that calling the .touch method of the PlayerManager
        updates the 'last_seen' field of a given Player with
        the current time.
        """

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

        # last_seen = create_datetime()

        channel_name = "player_channel"
        player = Player.objects.create(
            auth_user=auth_user,
            room=room,
            channel_name=channel_name
        )

        test_timezone = timezone.now()
        patched_time.return_value = test_timezone


        # Update last_seen timestamp
        Player.objects.touch(channel_name)

        player.refresh_from_db()

        updated_player = Player.objects.get(id=player.id)

        patched_time.assert_called_once()
        self.assertEqual(updated_player.last_seen, test_timezone)

    def test_leave_room(self):
        """
        Test that the 'prune_rooms' method of RoomManager 
        deletes 
        """

        room_name = "test_room"

        room = Room.objects.create(room_name=room_name)

        test_user_1 = create_user()
        user_channel_name_1 = "user_channel_1"
        player_1 = room.add_player(
            channel_name=user_channel_name_1,
            user=test_user_1
        )

        test_user_2 = create_user(email="user2@example.com")
        user_channel_name_2 = "user_channel_2"
        player_2 = room.add_player(
            channel_name=user_channel_name_2,
            user=test_user_2
        )

        player_list = room.player_set.all()
        assert len(room.player_set.all()) == 2
        assert player_1 in player_list
        assert player_2 in player_list

        # Simulate actions when player disconnects.
        Player.objects.leave_rooms(user_channel_name_1)

        updated_room = Room.objects.get(room_name=room_name)

        updated_player_list = updated_room.player_set.all()

        assert player_1 not in updated_player_list
        assert player_2 in updated_player_list
        assert len(updated_player_list) == 1
