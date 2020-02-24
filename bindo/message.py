"""This module provides API for packing and unpacking messages."""
import struct
import hashlib
from typing import Dict, Union


class MessageFactory(object):

    def __init__(self, buffer: bytes) -> None:
        self.buffer = buffer

    def append_buffer(self, buffer: bytes) -> None:
        self.buffer += buffer

    def get_buffer(self) -> bytes:
        return self.buffer

    def get_buffer_size(self) -> int:
        return len(self.buffer)


class MessageWriter(MessageFactory):

    def __init__(self) -> None:
        buffer = bytes()
        super().__init__(buffer)

    def pack_character(self, value: str) -> None:
        self.buffer += struct.pack('<s', bytes(value, 'latin-1'))

    def pack_integer(self, value: int) -> None:
        self.buffer += struct.pack('<i', value)

    def pack_string(self, value: str) -> None:
        value_len = len(value)
        self.buffer += struct.pack(
            f'<i{value_len}s',
            value_len,
            bytes(value, 'latin-1')
        )

    # TODO: pack_bool, pack_large_integer.


class MessageReader(MessageFactory):

    def __init__(self, buffer: bytes) -> None:
        self.pointer = 0
        super().__init__(buffer)

    def unpack_character(self) -> str:
        (value,) = struct.unpack(
            '<s',
            self.buffer[self.pointer:self.pointer + 1]
        )
        self.pointer += 1
        return value.decode('latin-1')

    def unpack_integer(self) -> int:
        (value,) = struct.unpack(
            '<i',
            self.buffer[self.pointer:self.pointer + 4]
        )
        self.pointer += 4
        return value

    def unpack_string(self) -> str:
        value_len = self.unpack_integer()
        (value,) = struct.unpack(
            f'<{value_len}s',
            self.buffer[self.pointer:self.pointer + value_len]
        )
        self.pointer += value_len
        return value.decode('latin-1')

    # TODO: unpack_book, unpack_large_integer


class Message(object):

    @staticmethod
    def construct_message(message_code: int, buffer: bytes) -> bytes:
        buffer_len = len(buffer) + 4
        message = MessageWriter()
        message.pack_integer(buffer_len)
        message.pack_integer(message_code)
        message.append_buffer(buffer)
        return message.get_buffer()

    @staticmethod
    def create_message(message_code: int, **kwargs: Union[str, int]) -> bytes:
        message = messages[message_code]
        message = message(**kwargs)
        return message.pack_message()

    @staticmethod
    def unpack_message(message_code: int, buffer: bytes) -> Dict[str, Union[str, int]]:
        if message_code not in messages:
            return {"code": "unknown"}
        message = messages[message_code]
        return message.unpack_message(buffer)


class Login(Message):

    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        md5 = hashlib.md5()
        md5.update(
            bytes(self.username, 'latin-1') + bytes(self.password, 'latin-1')
        )
        self.hexdigest = md5.hexdigest()
        self.version = 182
        self.minor_version = 157

    def pack_message(self) -> bytes:
        message = MessageWriter()
        message.pack_string(self.username)
        message.pack_string(self.password)
        message.pack_integer(self.version)
        message.pack_string(self.hexdigest)
        message.pack_integer(self.minor_version)
        return self.construct_message(1, message.get_buffer())

    @staticmethod
    def unpack_message(buffer: bytes) -> Dict[str, Union[str, int]]:
        message = MessageReader(buffer)
        _ = message.unpack_integer()
        code = message.unpack_integer()
        if code:
            greet = message.unpack_string()
            ip = message.unpack_integer()
            return {"code": code, "greet": greet, "ip": ip}
        else:
            reason = message.unpack_string()
            raise ConnectionError(reason)


class SetListenPort(Message):

    def __init__(self, port: int) -> None:
        self.port = port

    def pack_message(self) -> bytes:
        message = MessageWriter()
        message.pack_integer(self.port)
        return self.construct_message(2, message.get_buffer())


class GetPeerAddress(Message):

    def __init__(self, username: str) -> None:
        self.username = username

    def pack_message(self) -> bytes:
        message = MessageWriter()
        message.pack_string(self.username)
        return self.construct_message(3, message.get_buffer())

    @staticmethod
    def unpack_message(buffer: bytes) -> Dict[str, Union[str, int]]:
        message = MessageReader(buffer)
        _ = message.unpack_integer()
        code = message.unpack_integer()
        username = message.unpack_string()
        ip = message.unpack_integer()
        port = message.unpack_integer()
        return {"code": code, "username": username, "ip": ip, "port": port}


class ConnectToPeer(Message):

    def __init__(self, token: int, username: str, type: str) -> None:
        self.token = token
        self.username = username
        self.type = type

    def pack_message(self) -> bytes:
        message = MessageWriter()
        message.pack_integer(self.token)
        message.pack_string(self.username)
        message.pack_string(self.type)
        return self.construct_message(18, message.get_buffer())

    @staticmethod
    def unpack_message(buffer: bytes) -> Dict[str, Union[str, int]]:
        message = MessageReader(buffer)
        _ = message.unpack_integer()
        code = message.unpack_integer()
        username = message.unpack_string()
        type = message.unpack_string()
        ip = message.unpack_integer()
        port = message.unpack_integer()
        token = message.unpack_integer()
        # priviledged = message.unpack_bool()
        return {
            "code": code,
            "username": username,
            "type": type,
            "ip": ip,
            "port": port,
            "token": token
        }


class SetStatus(Message):

    def __init__(self, status: int) -> None:
        self.status = status

    def pack_message(self) -> bytes:
        message = MessageWriter()
        message.pack_integer(self.status)
        return self.construct_message(28, message.get_buffer())


class SharedFoldersFiles(Message):

    def __init__(self, dirs: int, files: int) -> None:
        self.dirs = dirs
        self.files = files

    def pack_message(self) -> bytes:
        message = MessageWriter()
        message.pack_integer(self.dirs)
        message.pack_integer(self.files)
        return self.construct_message(35, message.get_buffer())


class CannotConnect(Message):

    def __init__(self, token: int, username: str) -> None:
        self.token = token
        self.username = username

    def pack_message(self) -> bytes:
        message = MessageWriter()
        message.pack_token(self.token)
        message.pack_username(self.username)
        return self.construct_message(1001, message.get_buffer())

    @staticmethod
    def unpack_message(buffer: bytes) -> Dict[str, Union[str, int]]:
        message = MessageReader(buffer)
        _ = message.unpack_integer()
        code = message.unpack_integer()
        token = message.unpack_integer()
        # username = message.unpack_string()
        return {"code": code, "token": token}


class PeerInitMessage(Message):
    """This class represents Peer Init Message.

    The difference between a PeerInitMessage and a normal Message is that the
    code part is only 1 byte long.
    """

    @staticmethod
    def construct_message(message_code: int, buffer: bytes) -> bytes:
        buffer_len = len(buffer) + 1
        message = MessageWriter()
        message.pack_integer(buffer_len)
        message.pack_character(message_code)
        message.append_buffer(buffer)
        return message.get_buffer()

    @staticmethod
    def create_message(message_code: int, **kwargs: Union[str, int]) -> bytes:
        message = peer_messages[message_code]
        message = message(**kwargs)
        return message.pack_message()

    @staticmethod
    def unpack_message(message_code: int, buffer: bytes) -> Dict[str, Union[str, int]]:
        if message_code not in peer_messages:
            return {"code": "unknown"}
        message = peer_messages[message_code]
        return message.unpack_message(buffer)


class PierceFirewall(PeerInitMessage):

    def __init__(self, token: int) -> None:
        self.token = token

    def pack_message(self) -> bytes:
        message = MessageWriter()
        message.pack_integer(self.token)
        return self.construct_message(0, message.get_buffer())

    @staticmethod
    def unpack_message(buffer: bytes) -> Dict[str, int]:
        message = MessageReader(buffer)
        _ = message.unpack_integer()
        code = message.unpack_character()
        token = message.unpack_integer()
        return {"code": int(code), "token": token}


class PeerInit(PeerInitMessage):

    def __init__(self, username: str, type: str, token: int) -> None:
        self.username = username
        self.type = type
        self.token = token

    def pack_message(self) -> bytes:
        message = MessageWriter()
        message.pack_string(self.username)
        message.pack_type(self.type)
        massage.pack_token(self.token)
        return self.construct_message(1, message.get_buffer())

    @staticmethod
    def unpack_message(buffer: bytes) -> Dict[str, Union[str, int]]:
        message = MessageReader(buffer)
        _ = message.unpack_integer()
        code = message.unpack_character()
        username = message.unpack_string()
        type = message.unpack_string()
        token = message.unpack_integer()
        return {
            "code": int(code),
            "username": username,
            "type": type,
            "token": token
        }


messages = {
    1: Login,
    2: SetListenPort,
    3: GetPeerAddress,
    18: ConnectToPeer,
    28: SetStatus,
    35: SharedFoldersFiles,
    1001: CannotConnect
}


peer_messages = {
    0: PierceFirewall,
    1: PeerInit
}
