import time
import socket
import threading
from typing import Dict, Union, Type, Tuple
from queue import Queue

from .listen import Listen
from .message import Message, PeerMessage
from .peer import Peer
from .server import Server


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
        # Might be usefull to put those into a seperate method.
        self.server_message(1, username=self.username, password=self.password)
        self.server_message(2, port=self.listen_port)
        self.server_message(28, status=2)
        self.server_message(35, dirs=10, files=250)

        while True:
            message = self.outgoing_messages.get(block=True)
            if message.get('recipient') == self.server:
                self.server.send(message['message'])
                time.sleep(0.05)  # TODO: Remove maybe.
            else:
                token = message.get('recipient')
                print(f'[CLIENT]: Sending message to peer (token={token}).')
                peer = self.peers.get(token)
                peer.send(message.get('message'))

    def handle_message(self, message: Dict[str, Union[str, int]]) -> None:
        if message.get('code') == 1:
            print('[CLIENT]: Successfully logged in.')
        elif message.get('code') == 'unknown':
            print(f"[CLIENT]: Recieved unknown message (message_code={message.get('message_code')}).")

    def handle_peer(self, message: Dict[str, Union[str, int]], token: int) -> None:
        print(f"[CLIENT]: Recieved message from peer (message_code={message.get('code')}, token={token}).")
        if message.get('code') == 5:
            print(message.get('dirs'))

    def handle_socket(self, socket: Type[socket.socket], address: Tuple[str, int], token) -> None:
        print(f'[CLIENT]: Received new socket (address={address}, token={token})')
        peer = Peer(socket, token, self.handle_peer)
        peer.start()
        self.peers.update({token: peer})

    def server_message(self, message_code: int, **kwargs: Dict[str, Union[str, int]]) -> None:
        message = Message.create_message(message_code, **kwargs)
        self.outgoing_messages.put({"recipient": self.server, "message": message})

    def peer_message(self, token, message_code: int, **kwargs: Dict[str, Union[str, int]]) -> None:
        if self.connection_established(token):
            message = PeerMessage.create_message(message_code, **kwargs)
            self.outgoing_messages.put({"recipient": token, "message": message})
        else:
            print(f"[CLIENT]: Can't send a message to peer (token={token})")

    def connection_established(self, token: int) -> bool:
        peer = self.peers.get(token)
        if peer and peer.is_alive():
            return True
        return False

    def attempt_sending(self, token: int, message_code: int,
                        tries: int = 10, **kwargs: Dict[str, Union[str, int]]) -> None:
        while True:
            if self.connection_established(token):
                self.peer_message(token, message_code, **kwargs)
                break
            elif not tries:
                break
            else:
                tries -= 1
                time.sleep(0.2)
