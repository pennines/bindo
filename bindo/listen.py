import socket
import threading


class Listen(threading.Thread):

    def __init__(self, port: int) -> None:
        self.buffer = bytes()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
            data = socket.recv(4096)
            if not data:
                continue

            # self.buffer += data
            self.buffer += data
            message_len = int.from_bytes(self.buffer[:4], 'little')
            (message_len,) = struct.unpack('<i', self.buffer[:4])
            if len(self.buffer) >= message_len:
                message_code = int.from_bytes(self.buffer[4:5], 'little')
