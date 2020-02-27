import socket
import threading
from typing import Callable, Type, Tuple


class Listen(threading.Thread):

    def __init__(self, port: int,
                 callback: Callable[[Type[socket.socket], Tuple[str, int]], None]) -> None:
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
            # PierceFirewall message (recieve it and do nothing with it.)
            _ = socket.recv(64)

            # Send a socket via callback.
            self.callback(socket, address)
