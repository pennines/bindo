import time
import socket
from typing import Dict, Union, Type, Tuple

from .listen import Listen
from .server import Server
from .message import Message


class Client(object):

    def __init__(self, username: str, password: str) -> None:
        self.server_address = 'server.slsknet.org'
        self.server_port = 2242
        self.listen_port = 2234

        self.username = username
        self.password = password

        self.logged_in = False

        self.server = Server(self.server_address, self.server_port, self.handle_message)
        self.listen = Listen(self.listen_port, self.handle_socket)

        self.server.start()
        self.listen.start()

    def handle_message(self, message: Dict[str, Union[str, int]]) -> None:
        if message.get('code') == 1:
            print('[CLIENT]: Successfully logged in.')
            self.logged_in = True
        elif message.get('code') == 'unknown':
            print(f"[CLIENT]: Recieved unknown message ({message.get('message_code')}).")

    def handle_socket(self, socket: Type[socket.socket], address: Tuple[str, int]) -> None:
        print(socket, address)

    def server_message(self, message_code: int, **kwargs: Dict[str, Union[str, int]]) -> None:
        message = Message.create_message(message_code, **kwargs)
        self.server.send(message)

    def login(self) -> None:
        if self.logged_in:
            print('[CLIENT]: User already logged in.')
            return

        login_messages = []
        # TODO: Config file.
        login_messages.append(Message.create_message(1, username=self.username, password=self.password))
        login_messages.append(Message.create_message(2, port=self.listen_port))
        login_messages.append(Message.create_message(28, status=2))
        login_messages.append(Message.create_message(35, dirs=10, files=250))

        for message in login_messages:
            self.server.send(message)
            time.sleep(0.05)  # maybe that's unnecessary
