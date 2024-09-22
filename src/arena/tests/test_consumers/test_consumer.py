import pytest

from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from app.asgi import application

from arena.models import Room, Player


TEST_CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

@database_sync_to_async
def create_user_with_token():
    user = get_user_model().objects.create_user(
        email="test@example.com", password="Testpass123!"
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
class TestWebsocket:
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
    def _test_room_exists_and_player_added(self, channel_name):
        """
        This function accompanies the async test function:
        "test_room_db_object_created_with_auth_user_added_as_player"

        DB transactions and required assertions aren't supported within
        an async function, therefore need to be moved to an external
        synchronous function.
        """
        room = Room.objects.filter(channel_name=channel_name)
        assert room.exists() == True
        
        auth_user = get_user_model().objects.get(player__room=room[0])
        auth_email = "test@example.com"
        assert auth_user.email == auth_email

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

        channel_name = "chess_test"
        await self._test_room_exists_and_player_added(channel_name)
    
        await communicator.disconnect()
