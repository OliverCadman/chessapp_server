import json
from json.decoder import JSONDecodeError

from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync


class ArenaConsumer(JsonWebsocketConsumer):
    def connect(self) -> None:
     
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chess_{self.room_id}"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()


    def disconnect(self, code):
        pass

    def receive(self, text_data) -> None:
        try:
            json_data = json.loads(text_data)
            self.send(json_data)
        except JSONDecodeError as e:
            self.send(f"Received badly formed JSON")





