from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.db.models import Q
from common.tests.constants import TEST_CHANNEL_LAYERS
from common.tests.utils import acreate_user_with_token, create_user

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

    # Util functions for DB transactions in test_list_connected_players
    @database_sync_to_async
    def create_and_return_test_room(self, test_room_group_name):
        return Room.objects.create(
            room_name=test_room_group_name
        )
    
    @database_sync_to_async
    def create_test_user(self, email):
        return create_user(
            email=email
        )
    
    @database_sync_to_async
    def add_players_to_room(self, room, players):
        [
            room.add_player(player["channel_name"], player["auth_user"])
            for player in players 
        ]

    async def test_list_connected_players(self, settings, origin_headers):
        """
        Test request to webocket to list connected players returns list of players
        in JSON.
        """

        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        test_room_group_name = "room_lobby_1"
        test_room = await self.create_and_return_test_room(test_room_group_name)

        test_user_1 = await self.create_test_user(
            email="test1@example.com"
        )
        test_user_1_channel_name = "user_1_channel"
    

        test_user_2 = await self.create_test_user(
            email="test2@example.com"
        )
        test_user_2_channel_name = "user_2_channel"

        test_user_3 = await self.create_test_user(
            email="test3@example.com"
        )
        test_user_3_channel_name = "user_3_channel"

        # Create 1-2-1 Player object for all three users.
        players_to_add_to_room = [
            {
                "channel_name": test_user_1_channel_name,
                "auth_user": test_user_1
            },
            {
                "channel_name": test_user_2_channel_name,
                "auth_user": test_user_2 
            },
            {
                "channel_name": test_user_3_channel_name,
                "auth_user": test_user_3
            }
        ]
        
        await self.add_players_to_room(test_room, players_to_add_to_room)

        current_user, token = await acreate_user_with_token()

        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby/{lobby_room_id}?token={token}",
            headers=[origin_headers]
        )

        connected, _ = await communicator.connect()
        assert connected is True

        payload = {
            "group_name": f"room_{lobby_room_id}",
            "type": "player.list",
            "data": {
                "current_user_email": current_user.email
            }
        }

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"room_{lobby_room_id}", payload
        )

        res = await communicator.receive_json_from()

        expected_res = [
                {
                    "user": {
                        "email": test_user_1.email
                    }
                },
                {
                    "user": {
                        "email": test_user_2.email
                    }
                },
                {
                    "user": {
                        "email": test_user_3.email
                    }
                }
            ]
        
        assert res["data"]["players"] == expected_res
        await communicator.disconnect()

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
            "group_name": user_group_name,
            "type": "lobby.challenge",
            "data": {
                "colour": enums.Colours.WHITE.value,
                "time_control": enums.TimeControls.RAPID.value
            }
        }

        await challenger_communicator.send_json_to(
            data=payload
        )

        res = await opponent_communicator.receive_json_from()

        expected_res = {
            "type": "lobby.challenge",
            "data": {
                "colour": enums.Colours.WHITE.value,
                "time_control": enums.TimeControls.RAPID.value
            }
        }
        assert res == expected_res

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
            "group_name": challenger_group_name,
            "type": "challenge.change.request",
            "data": {
                "colour": enums.Colours.RANDOM.value,
                "time_control": enums.TimeControls.SUPERBLITZ.value
            }
        }

        await opponent_communicator.send_json_to(
            data=opponent_change_request_payload
        )

        change_res = await challenger_communicator.receive_json_from()

        expected_res = {
            "type": "challenge.change.request",
            "data": {
                "colour": enums.Colours.RANDOM.value,
                "time_control": enums.TimeControls.SUPERBLITZ.value
            }
        }

        assert change_res == expected_res

        await challenger_communicator.disconnect()
        await opponent_communicator.disconnect()

    @database_sync_to_async
    def assert_expected_player_list_length(self, room, expected_list_length):
        player_list = room.player_set.all()
        assert len(player_list) == expected_list_length

    @database_sync_to_async
    def assert_players_in_player_list(self, room, players):
        player_list = room.player_set.all()
        for player in players:
            assert player in player_list

    @database_sync_to_async
    def assert_player_not_in_list(self, room, player):
        player_list = room.player_set.all()
        assert player not in player_list

    @database_sync_to_async
    def get_player_by_email(self, email):
        return Player.objects.get(auth_user__email=email)
    
    @database_sync_to_async
    def get_all_players(self):
        return Player.objects.all()
    
    @database_sync_to_async
    def get_all_players_except_disconnected_user(self, email):
        return Player.objects.filter(~Q(auth_user__email=email))

    async def test_player_pruned_from_room_upon_disconnect(self, settings, origin_headers):
        """
        Test that a Player instance is removed from associated Room instance
        upon Websocket disconnect.
        """

        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        test_room_group_name = "room_lobby_1"
        test_room = await self.create_and_return_test_room(test_room_group_name)

        test_user_1 = await self.create_test_user(
            email="test1@example.com"
        )
        test_user_1_channel_name = "user_1_channel"
    

        test_user_2 = await self.create_test_user(
            email="test2@example.com"
        )
        test_user_2_channel_name = "user_2_channel"

        # Create 1-2-1 Player object for all three users.
        players_in_room = [
            {
                "channel_name": test_user_1_channel_name,
                "auth_user": test_user_1
            },
            {
                "channel_name": test_user_2_channel_name,
                "auth_user": test_user_2 
            }
        ]
        
        await self.add_players_to_room(test_room, players_in_room)

        test_user_3, token = await acreate_user_with_token()

        communicator = WebsocketCommunicator(
            application=application,
            path=f"ws/lobby/{lobby_room_id}?token={token}",
            headers=[origin_headers]
        )
        
        connected, _ = await communicator.connect()
        assert connected is True

        connected_player = await self.get_player_by_email(test_user_3.email)
        
        players_in_room.append({
            "channel_name": connected_player.channel_name,
            "auth_user": test_user_3
        })

        await self.assert_expected_player_list_length(test_room, 3)

        all_players = await self.get_all_players()
        
        await self.assert_players_in_player_list(test_room, all_players)
        await communicator.disconnect()

        del players_in_room[-1]

        all_players_except_disconnected_user = await self.get_all_players_except_disconnected_user(
            test_user_3.email
            )

        await self.assert_player_not_in_list(test_room, connected_player)
        await self.assert_expected_player_list_length(test_room, 2)
        await self.assert_players_in_player_list(test_room, all_players_except_disconnected_user)

        
