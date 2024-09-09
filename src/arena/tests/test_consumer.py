from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from arena.routing import websocket_urlpatterns
from django.test import TestCase
from arena.consumers import ArenaConsumer

import json


router = URLRouter(websocket_urlpatterns)


class ArenaConsumerTests(TestCase):

    async def testConnection(self):
        """
        Test successful Webhook connection
        """
        self.communicator = WebsocketCommunicator(router, "ws/arena/test")
        connected, _ = await self.communicator.connect()
        self.assertTrue(connected)

        self.communicator.disconnect()

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
        self.communicator.disconnect()

    async def testJoinRedisChannel(self):
        self.communicator = WebsocketCommunicator(router, "ws/arena/test")
        await self.communicator.connect()
