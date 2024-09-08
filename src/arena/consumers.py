import json

from channels.generic.websocket import JsonWebsocketConsumer


class ArenaConsumer(JsonWebsocketConsumer):
    def connect(self):
        print("hiii")
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, text_data):
        print(text_data)


