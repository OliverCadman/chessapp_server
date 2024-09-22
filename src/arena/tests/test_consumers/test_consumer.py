import pytest

from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from app.asgi import application

TEST_CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

@pytest.fixture
def origin_headers():
    """
    Required to be passed as constructor arg to WebsocketCommunicator,
    since the WS app is wrapped by AllowedHostsOriginValidator.
    """
    return (b"origin", b"ws://127.0.0.1:8000")

@pytest.mark.asyncio
class TestWebsocket:
    async def test_connection_to_socket(self, settings, origin_headers):
        """
        Simply test if a connection to the ws path can be established.
        """

        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        communicator = WebsocketCommunicator(
            application=application, 
            path="ws/arena/test",
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

        communicator = WebsocketCommunicator(
            application=application,
            path="ws/arena/test",
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

        communicator = WebsocketCommunicator(
            application=application,
            path="ws/arena/test",
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
