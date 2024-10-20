from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async

from django.contrib.auth import get_user_model

from common.tests.constants import TEST_CHANNEL_LAYERS
from common.tests.utils import acreate_user_with_token

from app.asgi import application

from lobby import enums

import pytest

@pytest.fixture(scope="session")
def origin_headers():
    """
    Required to be passed as constructor arg to WebsocketCommunicator,
    since the WS app is wrapped by AllowedHostsOriginValidator.
    """
    return (b"origin", b"ws://127.0.0.1:8000")


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestLobbyWebsocket:
    async def test_authorized_user_connect_successful(
            self, settings, origin_headers
            ): 
        
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        _, token = await acreate_user_with_token()

        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby?token={token}",
            headers=[origin_headers]
        )

        connected, _ = await communicator.connect()
        assert connected is True

        await communicator.disconnect()

    async def test_unauthorized_user_disconnect(
            self, settings, origin_headers
            ):

        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS


        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby",
            headers=[origin_headers]
        )

        connected, _ = await communicator.connect()
        assert connected is False

        await communicator.disconnect()

    async def test_authorized_connect_creates_single_user_group(
            self, settings, origin_headers
            ):
        
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        user, token = await acreate_user_with_token()

        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby?token={token}",
            headers=[origin_headers]
        )

        connected, _ = await communicator.connect()

        user_group_name = f"user_{user.id}"
        channel_layer = get_channel_layer()

        assert connected is True
        assert user_group_name in channel_layer.groups

        await communicator.disconnect()

    async def test_send_challenge_to_another_player(
            self, settings, origin_headers
    ):
        
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        # First player
        _, challenger_token = await acreate_user_with_token()

        challenger_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby?token={challenger_token}",
            headers=[origin_headers]
        )

        await challenger_communicator.connect()

        # Second player
        opponent, opponent_token = await acreate_user_with_token(
            email="opponent@example.com", password="Testpass123!"
        )

        opponent_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby?token={opponent_token}",
            headers=[origin_headers]
        )

        await opponent_communicator.connect()

        # Player not involved in transaction
        _, another_player_token = await acreate_user_with_token(
            email="another@example.com", password="Testpass123!"
        )

        another_player_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby?token={another_player_token}",
            headers=[origin_headers]
        )

        await another_player_communicator.connect()

        room_group_name = f"user_{opponent.id}"

        payload = {
            "type": "lobby.challenge",
            "data": {
                "colour": enums.Colours.WHITE.value,
                "time_control": enums.TimeControls.RAPID.value,
                "group_name": room_group_name
            }
        }

        await challenger_communicator.send_json_to(
            data=payload
        )

        res = await opponent_communicator.receive_json_from()
        assert res == payload

        assert await another_player_communicator.receive_nothing() is True

        await challenger_communicator.disconnect()
        await opponent_communicator.disconnect()
        await another_player_communicator.disconnect()

    async def test_opponent_suggests_challenge_changes(
            self, settings, origin_headers
    ):
        
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        
        challenger, challenger_token = await acreate_user_with_token()

        challenger_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby?token={challenger_token}",
            headers=[origin_headers]
        )

        opponent, opponent_token = await acreate_user_with_token(
            email="opponent@example.com", password="Testpass123!"
        )

        opponent_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby?token={opponent_token}",
            headers=[origin_headers]
        )

        await challenger_communicator.connect()
        await opponent_communicator.connect()

        challenger_group_name = f"user_{challenger.id}"

        opponent_change_request_payload = {
            "type": "challenge.change.request",
            "data": {
                "group_name": challenger_group_name,
                "colour": enums.Colours.RANDOM.value,
                "time_control": enums.TimeControls.SUPERBLITZ.value
            }
        }

        await opponent_communicator.send_json_to(
            data=opponent_change_request_payload
        )

        change_res = await challenger_communicator.receive_json_from()
        assert change_res == opponent_change_request_payload

        await challenger_communicator.disconnect()
        await opponent_communicator.disconnect()
