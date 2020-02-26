import socket
import threading
from typing import Type, Tuple, Callable, Union, Dict

from .message import PeerMessage


class Peer(threading.Thread):

    def __init__(self, socket: Type[socket.socket],
                 callback: Callable[[Dict[str, Union[str, int]]], None]) -> None:
        self.buffer = bytes()
        self.callback = callback
        self.connection = socket
        super().__init__()
        self.daemon = True

    def send(self, message: bytes) -> None:
        self.connection.send(message)

    def run(self) -> None:
        while True:
            data = self.connection.recv(4096)

            self.buffer += data
            message_len = int.from_bytes(self.buffer[:4], 'little')
            if len(self.buffer) >= message_len:
                # TODO: There two types of messages that we can recieve from this socket.
                #   PeerMessage,
                #   PeerInitMessage,
                #   PeerMessage uses 4 bytes to indicate message code.
                #   PeerInitMessage uses 1 byte to indicate message code.
                #   HOW TO HANDLE THIS?
                message_code = int.from_bytes(self.buffer[4:5], 'little')
                message = PeerMessage.unpack_message(message_code, self.buffer)
                self.callback(message)
                self.buffer = self.buffer[message_len + 4:]
