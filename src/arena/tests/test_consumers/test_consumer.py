from channels.testing import WebsocketCommunicator

from channels.routing import URLRouter
from arena.routing import websocket_urlpatterns
from django.test import TestCase, Client
from arena.consumers import ArenaConsumer
from arena.tests.utils.test_helpers import create_test_user
from asgiref.sync import sync_to_async

import json



router = URLRouter(websocket_urlpatterns)


class ArenaConsumerUnitTests(TestCase):

    async def testConnection(self):
        """
        Test successful Webhook connection
        """
        self.communicator = WebsocketCommunicator(router, "ws/arena/test")
        connected, _ = await self.communicator.connect()
        self.assertTrue(connected)

        await self.communicator.disconnect()

    async def testSendAndReceiveJSON(self):
        """
        Test JSON is sent and emitted from webhook
        """

        self.communicator = WebsocketCommunicator(router, "ws/arena/test")
        await self.communicator.connect()

        test_payload = json.dumps({
            "message": "testing"
        })

        await self.communicator.send_json_to(data=test_payload)
        response = await self.communicator.receive_from()
        json_response = json.loads(response)

        decoded_test_payload = json.loads(test_payload)

        self.assertEqual(json_response, decoded_test_payload)
        await self.communicator.disconnect()

    async def testJoinRedisChannel(self):
        self.communicator = WebsocketCommunicator(router, "ws/arena/test")
        await self.communicator.connect()


class ArenaConsumerIntegrationTests(TestCase):
    """
    1. Test Room object created with Authenticated Player on connection.
    """

    async def test_room_object_created_with_auth_user_on_connect(self):

        auth_user = await sync_to_async(create_test_user)()

        client = Client()
        await sync_to_async(client.force_login)(auth_user)
        self.assertTrue(auth_user.is_authenticated)
        

        self.communicator = WebsocketCommunicator(router, "ws/arena/test")
        await self.communicator.connect()
        await self.communicator.disconnect()
