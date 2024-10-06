import pytest

from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from app.asgi import application

from lobby.models import Room, Player


TEST_CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

@database_sync_to_async
def create_user_with_token(email="test@example.com", password="Testpass123!"):
    user = get_user_model().objects.create_user(
        email=email, password=password
    )

    access = AccessToken.for_user(user)
    return user, access


@pytest.fixture
def origin_headers():
    """
    Required to be passed as constructor arg to WebsocketCommunicator,
    since the WS app is wrapped by AllowedHostsOriginValidator.
    """
    return (b"origin", b"ws://127.0.0.1:8000")


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestArenaWebsocket:
    async def test_authorized_connection_to_socket(self, settings, origin_headers):
        """
        Simply test if a connection to the ws path can be established.
        """

        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        _, token = await create_user_with_token()

        communicator = WebsocketCommunicator(
            application=application, 
            path=f"ws/arena/test?token={token}",
            headers=[
                origin_headers
            ]
        )
        connected, _ = await communicator.connect()
        assert connected is True
        await communicator.disconnect()

    async def test_send_and_receive_messages(self, settings, origin_headers):
        """
        Test if a message can be sent to and received from websocket path.
        """

        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        _, token = await create_user_with_token()

        communicator = WebsocketCommunicator(
            application=application, 
            path=f"ws/arena/test?token={token}",
            headers=[
                origin_headers
            ]
        )

        connected, _ = await communicator.connect()
        assert connected is True

        payload = {
            "type": "echo.message",
            "data": "test message"
        }

        await communicator.send_json_to(payload)
        res = await communicator.receive_json_from()
        assert res == payload

        await communicator.disconnect()

    async def test_send_receive_messages_to_group(self, settings, origin_headers):
        """
        Test if a message can be broadcast to, and received from a channels group.
        """

        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        _, token = await create_user_with_token()

        communicator = WebsocketCommunicator(
            application=application, 
            path=f"ws/arena/test?token={token}",
            headers=[
                origin_headers
            ]
        )

        connected, _ = await communicator.connect()
        assert connected is True

        payload = {
            "type": "echo.message",
            "data": "test message"
        }

        channel_layer = get_channel_layer()

        # Prefix 'chess_' is prepended to 'test', which is passed as query param.
        room_group_name = "chess_test"
        await channel_layer.group_send(room_group_name, message=payload)

        res = await communicator.receive_json_from()
        assert res == payload

        await communicator.disconnect()

    async def test_unauthorized_connection_not_allowed(self, settings, origin_headers):

        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        communicator = WebsocketCommunicator(
            application=application,
            path="ws/arena/test",
            headers=[origin_headers]
        )

        connected, _ = await communicator.connect()
        assert connected is False
        await communicator.disconnect()

    @database_sync_to_async
    def _assert_room_exists_and_player_added(self, room_name):
        """
        This function accompanies the async test function:
        "test_room_db_object_created_with_auth_user_added_as_player"

        DB transactions and required assertions aren't supported within
        an async function, therefore need to be moved to an external
        synchronous function.
        """
        room = Room.objects.filter(room_name=room_name)
        assert room.exists() == True
        
        auth_user = get_user_model().objects.get(player__room=room[0])
        auth_email = "test@example.com"
        assert auth_user.email == auth_email

        return room[0].id

    async def test_room_db_object_created_with_auth_user_added_as_player(
            self, settings, origin_headers
            ):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        _, token = await create_user_with_token()

        
        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/arena/test?token={token}",
            headers=[
                origin_headers
                ]
        )

        await communicator.connect()

        room_name = "chess_test"
        await self._assert_room_exists_and_player_added(room_name)
    
        await communicator.disconnect()

    @database_sync_to_async
    def _assert_room_contains_two_players(self, room_name):
        """
        Synchronous testutil function to accompany below functions:

        - "test_two_players_in_same_room_upon_connect"

        - "test_third_player_cannot_connect_to_socket_room_containing_two_players"
        """

        room = Room.objects.get(room_name=room_name)
        number_of_players_in_room = 2
        
        assert len(room.player_set.all()) == number_of_players_in_room

    async def test_two_players_in_same_room_upon_connect(
            self, settings, origin_headers
    ):
        """
        Test that when two players join a room using the same room ID,
        their respective Player objects are added to the same corresponding
        Room object.
        """
        
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        # First Player
        _, first_player_token = await create_user_with_token(
            email="first@example.com",
            password="Testpass123!"
        )

        first_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/arena/test?token={first_player_token}",
            headers=[origin_headers]
        )

        first_player_connected, _ = await first_communicator.connect()
        assert first_player_connected == True

        # Second player
        _, second_player_token = await create_user_with_token(
            email="second@example.com",
            password="Testpass123!"
        )

        second_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/arena/test?token={second_player_token}",
            headers=[origin_headers]
        )

        second_player_connected, _ = await second_communicator.connect()
        assert second_player_connected == True

        room_name = "chess_test"
        await self._assert_room_contains_two_players(room_name)

        await first_communicator.disconnect()
        await second_communicator.disconnect()

    async def test_third_player_cannot_connect_to_socket_room_containing_two_players(
            self, settings, origin_headers
    ):
        """
        Test that a RoomFullException is raised when a third
        player attempts to join a Room at capacity.
        """
        
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        # First Player
        _, first_player_token = await create_user_with_token(
            email="first@example.com",
            password="Testpass123!"
        )

        first_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/arena/test?token={first_player_token}",
            headers=[origin_headers]
        )

        first_player_connected, _ = await first_communicator.connect()
        assert first_player_connected == True

        # Second player
        _, second_player_token = await create_user_with_token(
            email="second@example.com",
            password="Testpass123!"
        )

        second_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/arena/test?token={second_player_token}",
            headers=[origin_headers]
        )

        second_player_connected, _ = await second_communicator.connect()
        assert second_player_connected == True

        room_name = "chess_test"
        await self._assert_room_contains_two_players(room_name)

        # Third player
        _, third_player_token = await create_user_with_token(
            email="third@example.com",
            password="Testpass123!"
        )

        third_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/arena/test?token={third_player_token}",
            headers=[origin_headers]
        )

        third_player_connected, _ = await third_communicator.connect()
        assert third_player_connected == False

        room_name = "chess_test"
        await self._assert_room_contains_two_players(room_name)

        await first_communicator.disconnect()
        await second_communicator.disconnect()
        await third_communicator.disconnect()

    @database_sync_to_async
    def _assert_room_contains_no_players(self, room_id):
        room = Room.objects.filter(id=room_id)
        assert room[0].is_empty

    @database_sync_to_async
    def _assert_one_player_created(self):
        assert len(Player.objects.all()) == 1

    @database_sync_to_async
    def _assert_no_players_exist(self):
        assert len(Player.objects.all()) == 0
        
    async def test_player_removed_from_room_upon_disconnect(
            self, settings, origin_headers
    ): 
        """
        Test that a player object is removed from the room
        when auth_user disconnected from the socket.
        """
        
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        _, token = await create_user_with_token()
        
        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/arena/test?token={token}",
            headers=[origin_headers]
        )

        await communicator.connect()
        await self._assert_one_player_created()

        await communicator.disconnect()
        await self._assert_no_players_exist()

    @database_sync_to_async
    def _assert_one_room_exists(self):
        assert len(Room.objects.all()) == 1

    @database_sync_to_async
    def _assert_room_deleted(self):
        assert len(Room.objects.all()) == 0

    async def test_room_deleted_when_emptied(
            self, settings, origin_headers
    ):
        """
        Test that a Room DB object is deleted
        when the final remaining player in the room has disconnected
        from the socket.
        """
        
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        _, token = await create_user_with_token()
        
        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/arena/test?token={token}",
            headers=[origin_headers]
        )

        await communicator.connect()
        await self._assert_one_player_created()
        await self._assert_one_room_exists()

        await communicator.disconnect()
        await self._assert_room_deleted()
