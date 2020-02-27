import time
import socket
import threading
from typing import Dict, Union, Type, Tuple
from queue import Queue

from .listen import Listen
from .server import Server
from .message import Message


class Client(threading.Thread):

    def __init__(self, username: str, password: str) -> None:
        self.server_address = 'server.slsknet.org'
        self.server_port = 2242
        self.listen_port = 2234

        self.username = username
        self.password = password

        self.outgoing_messages = Queue()
        self.peers = {}

        self.server = Server(self.server_address, self.server_port, self.handle_message)
        self.listen = Listen(self.listen_port, self.handle_socket)

        self.server.start()
        self.listen.start()

        super().__init__()

    def run(self) -> None:
        # Might be usefull to put those into the seperate method.
        self.outgoing_messages.put(Message.create_message(1, username=self.username, password=self.password))
        self.outgoing_messages.put(Message.create_message(2, port=self.listen_port))
        self.outgoing_messages.put(Message.create_message(28, status=2))
        self.outgoing_messages.put(Message.create_message(35, dirs=10, files=250))

        while True:
            message = self.outgoing_messages.get(block=True)
            self.server.send(message)
            time.sleep(0.05)  # That might be unnecessary.

    def handle_message(self, message: Dict[str, Union[str, int]]) -> None:
        if message.get('code') == 1:
            print('[CLIENT]: Successfully logged in.')
        elif message.get('code') == 'unknown':
            print(f"[CLIENT]: Recieved unknown message ({message.get('message_code')}).")

    def handle_socket(self, socket: Type[socket.socket], address: Tuple[str, int]) -> None:
        print(socket, address)
        self.peers = {}

    def server_message(self, message_code: int, **kwargs: Dict[str, Union[str, int]]) -> None:
        message = Message.create_message(message_code, **kwargs)
        self.server.send(message)
