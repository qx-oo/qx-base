import six
import base64
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from django.conf import settings


class Signature(object):
    def __init__(self, key: str):
        self.key = key

    def pkcs7padding(self, data: str) -> str:
        bs = AES.block_size
        padding = bs - len(data) % bs
        padding_text = six.b(chr(padding) * padding)
        return data + padding_text

    def encrypt(self, raw: str) -> str:
        value = raw.encode()
        raw = self.pkcs7padding(value)
        cipher = AES.new(self.key, AES.MODE_ECB)
        return base64.b64encode(cipher.encrypt(raw))

    def get_md5(self, raw: str) -> str:
        return encode_md5(self.encrypt(raw))  # noqa

    def rsa_sign(self, data: str, decode=True) -> str:
        if decode:
            pri_key_str = base64.b64decode(self.key)
        else:
            pri_key_str = self.key
        pri_key = RSA.importKey(pri_key_str)
        signer = PKCS1_v1_5.new(pri_key)
        signature = signer.sign(SHA256.new(data.encode()))
        sign = base64.encodebytes(signature).decode().replace("\n", "")
        return sign

    def rsa_verify(self, sign: str, data: str, decode=True) -> bool:
        if decode:
            pub_key_str = base64.b64decode(self.key)
        else:
            pub_key_str = self.key
        pub_key = RSA.importKey(pub_key_str)
        verifier = PKCS1_v1_5.new(pub_key)
        data = SHA256.new(data.encode())
        return verifier.verify(data, base64.b64decode(sign))


class ApiSignature():
    public_key = settings.SIGNATURE_PUBLIC_KEY
    private_key = settings.SIGNATURE_PRIVATE_KEY

    def signature(self, json_str: str) -> str:
        return Signature(self.private_key).rsa_sign(json_str, decode=False)

    def verify(self, sign: str, json_str: str) -> bool:
        return Signature(self.public_key).rsa_verify(
            sign, json_str, decode=False)
