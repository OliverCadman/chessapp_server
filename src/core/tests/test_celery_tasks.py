from django.test import TestCase
from core.models import Room, Player
from core.tasks import prune_players

from common.tests.utils import create_user
from unittest.mock import patch

from datetime import timedelta, datetime


class TestCeleryTasks(TestCase):

    def setUp(self):
        """
        Mock datetime in order to simulate time passing.
        """
        self.datetime = datetime.now()
        class MockedDatetime(datetime):
            @classmethod
            def now(cls):
                return self.datetime
        patcher = patch("core.models.datetime", MockedDatetime)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_celery_prunes_player_after_60_seconds_inactivity(self):
        """
        Test if celery shared task calls Room.objects.prune_players()
        and deletes Player objects with a last_seen timestamp which
        is older than 60 seconds.

        Datetime object is mocked using the MockedDatetime object,
        to simulate passing of time.
        """
        
        room_name = "test_room"
        room = Room.objects.create(room_name=room_name)

        test_user_1 = create_user()
        user_channel_name_1 = "user_channel_1"
        player = room.add_player(
            channel_name=user_channel_name_1,
            user=test_user_1
        )

        player_list = room.player_set.all()
        self.assertEqual(len(player_list), 1)
        self.assertIn(player, player_list)
        
        seconds_since_player_inactivity = 65 # Max age is 60
        self.datetime = datetime.now() + timedelta(seconds=seconds_since_player_inactivity)

        prune_players.s().apply()
        
        updated_player_list = room.player_set.all()
        self.assertEqual(len(updated_player_list), 0)
        self.assertNotIn(player, updated_player_list)

    def test_celery_does_not_prune_player_within_60_seconds_inactivity(self):
        """
        Test if celery shared task calls Room.objects.prune_players()
        and does not prune players with a timestamp that is 'younger'
        than 60 seconds.
        """

        room_name = "test_room"
        room = Room.objects.create(room_name=room_name)

        test_user_1 = create_user()
        user_channel_name_1 = "user_channel_1"
        player = room.add_player(
            channel_name=user_channel_name_1,
            user=test_user_1
        )

        player_list = room.player_set.all()
        self.assertEqual(len(player_list), 1)
        self.assertIn(player, player_list)
        
        seconds_since_player_inactivity = 50 # Max age is 60
        self.datetime = datetime.now() + timedelta(seconds=seconds_since_player_inactivity)

        prune_players.s().apply()
        
        updated_player_list = room.player_set.all()
        self.assertEqual(len(updated_player_list), 1)
        self.assertIn(player, updated_player_list)

