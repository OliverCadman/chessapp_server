from abc import abstractmethod


class ServerException(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    @abstractmethod
    def __str__(self):
        pass


class RoomFullException(ServerException):
    def __init__(self, msg: str):
        super().__init__(msg)
    
    def __str__(self):
        return self.msg
    

class PlayerNotFoundException(ServerException):
    def __init__(self, msg: str):
        super().__init__(msg)
    
    def __str__(self):
        return self.msg
    

class RoomNotFoundException(ServerException):
    def __init__(self, msg: str):
        super().__init__(msg)
    
    def __str__(self):
        return self.msg
   