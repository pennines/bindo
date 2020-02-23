import socket
import threading
from typing import Callable, Dict, Type, Union

from .message import Message


class Server(threading.Thread):
    """This class represents a connection to the server.

    We can send a message and recieve response to this message. Each response
    is handled via callback.
    """

    def __init__(self, address: str, port: int,
                 callback: Callable[[Dict[str, Union[str, int]]], None]) -> None:
        self.buffer = bytes()
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((
            address or 'server.slsknet.org',
            port or 2242
        ))
        self.callback = callback
        super().__init__()

    def send(self, message: bytes) -> None:
        self.connection.send(message)

    def run(self) -> None:
        while True:
            data = self.connection.recv(4096)
            if not data:
                continue

            self.buffer += data
            message_len = int.from_bytes(self.buffer[:4], 'little')
            if len(self.buffer) >= message_len:
                message_code = int.from_bytes(self.buffer[4:8], 'little')
                message = Message.unpack_message(message_code, self.buffer)
                self.callback(message)
                self.buffer = self.buffer[message_len + 4:]
