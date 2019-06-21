# coding: utf-8
import base64
import zlib
from typing import Union


def unzip(base64data: Union[str, bytes]) -> bytes:
    return zlib.decompress(bytearray(ord(i) for i in base64.b64decode(base64data).decode()), -zlib.MAX_WBITS)
