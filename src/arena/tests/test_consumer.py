from channels.testing import WebsocketCommunicator
from django.test import TestCase
from arena.consumers import ArenaConsumer


class ArenaConsumerTests(TestCase):

    def setUp(self) -> None:
        self.communicator = WebsocketCommunicator(ArenaConsumer.as_asgi(), "ws/arena")

    async def testSocketConnection(self):
        connected, subprotocol = await self.communicator.connect()
        self.assertTrue(connected)

    def tearDown(self) -> None:
        self.communicator.disconnect()


