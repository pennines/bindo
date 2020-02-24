import socket
import threading


class Listen(threading.Thread):

    def __init__(self, port: int) -> None:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((socket.gethostname(), port))
        self.server.listen(1)
        super().__init__()
        self.daemon = True

    def run(self) -> None:
        while True:
            (socket, address) = self.server.accept()
            # Do something with this socket.
            # My guess is that we can recieve message such as "PeerInit" and
            # "PierceFirewall" from this socket.
