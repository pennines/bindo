"""This module provides API for packing and unpacking messages."""
import struct
import hashlib
from typing import Dict, Union


class MessageFactory(object):

    def append_buffer(self, buffer: bytes) -> None:
        self.buffer += buffer

    def get_buffer(self) -> bytes:
        return self.buffer

    def get_buffer_size(self) -> int:
        return len(self.buffer)


class MessageWriter(MessageFactory):

    def __init__(self) -> None:
        self.buffer = bytes()

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
        self.buffer = buffer
        self.pointer = 0
        # It's not as elegant as I want it to be but it works.

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

    def pack_message(self, message_code: int, buffer: bytes) -> bytes:
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
        return super().pack_message(1, message.get_buffer())

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


messages = {
    1: Login
}
