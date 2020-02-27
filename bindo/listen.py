import socket
import threading
from typing import Callable, Type, Tuple

from .message import PeerInitMessage


class Listen(threading.Thread):

    def __init__(self, port: int,
                 callback: Callable[[Type[socket.socket], Tuple[str, int], int], None]) -> None:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((socket.gethostname(), port))
        self.server.listen(1)
        self.callback = callback
        super().__init__()
        self.daemon = True

    def run(self) -> None:
        while True:
            # Listen for incoming connections, send an incoming connection via
            # callback.
            (socket, address) = self.server.accept()

            # PierceFirewall message (receive token and send it via callback)
            data = socket.recv(1024)
            message_code = int.from_bytes(data[4:5], 'little')

            # Check if we're, in fact, recieved PierceFirewall.
            if message_code == 0:
                message = PeerInitMessage.unpack_message(message_code, data)
                token = message.get('token')
                # Send a socket via callback.
                self.callback(socket, address, token)
