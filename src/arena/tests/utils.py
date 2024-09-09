from channels.generic.websocket import JsonWebsocketConsumer
from channels.testing import WebsocketCommunicator

class Connection:
    def __init__(self, url_path: str):
        self.url_path = url_path
    
    def connect(self, consumer: JsonWebsocketConsumer) -> WebsocketCommunicator: 
        return WebsocketCommunicator(consumer, self.url_path)
