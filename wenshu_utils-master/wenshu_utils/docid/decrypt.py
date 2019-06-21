# coding: utf-8
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

from ._unzip import unzip

IV = b"abcd134556abcedf"


def decrypt_doc_id(doc_id: str, key: bytes) -> str:
    result = unzip(doc_id)
    for _ in range(2):
        result = _decrypt(result, key)

    return result.decode()


def _decrypt(data: bytes, key: bytes, iv: bytes = IV) -> bytes:
    """pycryptodomex库解密"""
    cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
    plaintext = cipher.decrypt(bytes.fromhex(data.decode()))
    result = unpad(plaintext, AES.block_size)
    return result


def _decrypt2(data: bytes, key: bytes, iv: bytes = IV) -> bytes:
    """cryptography库解密"""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7
    from cryptography.hazmat.backends import default_backend

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(bytes.fromhex(data.decode())) + decryptor.finalize()

    pkcs7 = PKCS7(algorithms.AES.block_size)
    unpadder = pkcs7.unpadder()
    result = unpadder.update(decrypted) + unpadder.finalize()
    return result
