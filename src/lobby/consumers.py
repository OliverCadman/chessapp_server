from channels.generic.websocket import AsyncJsonWebsocketConsumer



class LobbyConsumer(AsyncJsonWebsocketConsumer):
    """
    Websocket event handler for chess arena lobby

    Events:
        - Player 1 submits game request to another player. Included data:
            - Time control
            - Colour
        
        - Player 2 accepts game request

        - Player 2 requests changes for either of the following:
            - Time control
            - Colour

            Player 1 accepts request

            Player 1 declines request

                Connection closes and game request needs to be re-submitted.

        - Player 2 declines request
    """



