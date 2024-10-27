from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from common.tests.constants import TEST_CHANNEL_LAYERS
from common.tests.utils import acreate_user_with_token

from core.models import Room, Player

from app.asgi import application

from lobby import enums

import pytest

lobby_room_id = "lobby_1"

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
            path=f"ws/lobby/{lobby_room_id}?token={token}",
            headers=[origin_headers]
        )

        connected, _ = await communicator.connect()
        assert connected is True

        await communicator.disconnect()

    @database_sync_to_async
    def assert_room_created_with_associated_player(self, user):
        room = Room.objects.get(player__auth_user=user)
        assert room.room_name == f"room_{lobby_room_id}"

        player = room.player_set.get(auth_user=user)
        assert player.auth_user.email == user.email

    async def test_authorized_connect_creates_room_with_player(self, settings, origin_headers):
        """
        Test Room object created with associated Player object
        upon connection to websocket.
        """

        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        user, token = await acreate_user_with_token()

        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby/{lobby_room_id}?token={token}",
            headers=[origin_headers]
        )

        connected, _ = await communicator.connect()
        assert connected is True

        await self.assert_room_created_with_associated_player(user)

        await communicator.disconnect()

    async def test_unauthorized_user_disconnect(
            self, settings, origin_headers
            ):

        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS


        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby/{lobby_room_id}",
            headers=[origin_headers]
        )

        connected, _ = await communicator.connect()
        assert connected is False

        await communicator.disconnect()

    async def test_list_connected_players(self, settings, origin_headers):
        """
        Test request to webocket to list connected players returns list of players
        in JSON.
        """

    async def test_authorized_connect_creates_single_user_group(
            self, settings, origin_headers
            ):
        
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        user, token = await acreate_user_with_token()

        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby/{lobby_room_id}?token={token}",
            headers=[origin_headers]
        )

        connected, _ = await communicator.connect()

        room_group_name = f"room_{lobby_room_id}"
        channel_layer = get_channel_layer()

        assert connected is True
        assert room_group_name in channel_layer.groups

        await communicator.disconnect()

    async def test_send_challenge_to_another_player(
            self, settings, origin_headers
    ):
        
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        # First player
        _, challenger_token = await acreate_user_with_token()

        challenger_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby/{lobby_room_id}?token={challenger_token}",
            headers=[origin_headers]
        )

        challenger_connected, _ = await challenger_communicator.connect()
        assert challenger_connected is True

        # Second player
        opponent, opponent_token = await acreate_user_with_token(
            email="opponent@example.com", password="Testpass123!"
        )

        opponent_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby/{lobby_room_id}?token={opponent_token}",
            headers=[origin_headers]
        )

        opponent_connected, _ = await opponent_communicator.connect()
        assert opponent_connected is True

        # Player not involved in transaction
        _, another_player_token = await acreate_user_with_token(
            email="another@example.com", password="Testpass123!"
        )

        another_player_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby/{lobby_room_id}?token={another_player_token}",
            headers=[origin_headers]
        )

        another_player_connected, _ = await another_player_communicator.connect()
        assert another_player_connected is True

        user_group_name = f"user_{opponent.id}"

        payload = {
            "type": "lobby.challenge",
            "data": {
                "colour": enums.Colours.WHITE.value,
                "time_control": enums.TimeControls.RAPID.value,
                "group_name": user_group_name
            }
        }

        await challenger_communicator.send_json_to(
            data=payload
        )

        res = await opponent_communicator.receive_json_from()
        assert res == payload

        # TODO: THIRD PLAYER SHOULD NOT RECEIVE CHALLENGE REQUEST.
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
            path=f"ws/lobby/{lobby_room_id}?token={challenger_token}",
            headers=[origin_headers]
        )

        _, opponent_token = await acreate_user_with_token(
            email="opponent@example.com", password="Testpass123!"
        )

        opponent_communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby/{lobby_room_id}?token={opponent_token}",
            headers=[origin_headers]
        )

        await challenger_communicator.connect()
        await opponent_communicator.connect()

        challenger_group_name = f"room_{lobby_room_id}"

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
