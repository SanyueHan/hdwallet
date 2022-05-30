from coincurve import PrivateKey

from hdwallet.public_key import PubKey


class PrvKey(PubKey):
    def __init__(self, private_key: bytes):
        self._private_key = PrivateKey(private_key)
        super().__init__(self._private_key.public_key.format())
