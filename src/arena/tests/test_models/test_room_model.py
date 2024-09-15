from django.test import TestCase
from django.contrib.auth import get_user_model
from arena.models import Room

from datetime import datetime


class RoomModelTests(TestCase):
    """
    - Creation of Room
    - Deletion of room
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
