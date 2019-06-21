# coding: utf-8
import hashlib
import random

from . import _vl5x


class Vjkl5(str):

    def __new__(cls, *args, **kwargs):
        return hashlib.sha1(str(random.random()).encode()).hexdigest()


class Vl5x(str):

    def __new__(cls, vjkl5: str):
        return _vl5x.get_vl5x(vjkl5)


class Number(str):

    def __new__(cls, *args, **kwargs):
        return "wens"


class Guid(str):

    def __new__(cls, *args, **kwargs):
        return cls._get_guid()

    @classmethod
    def _get_guid(cls) -> str:
        return "{}{}-{}-{}{}-{}{}{}".format(
            cls._create_guid(), cls._create_guid(),
            cls._create_guid(), cls._create_guid(),
            cls._create_guid(), cls._create_guid(),
            cls._create_guid(), cls._create_guid(),
        )

    @staticmethod
    def _create_guid() -> str:
        return hex(int((1 + random.random()) * 0x10000) | 0)[3:]
