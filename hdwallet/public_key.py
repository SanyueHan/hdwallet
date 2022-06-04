from bitsv.format import public_key_to_address, address_to_public_key_hash
from bitsv.transaction import OP_DUP, OP_HASH160, OP_PUSH_20, OP_EQUALVERIFY, OP_CHECKSIG
from coincurve import PublicKey

from hdwallet.network import NETWORK_API


class PubKey:
    def __init__(self, pub_key_bytes: bytes):
        self._public_key: PublicKey = PublicKey(pub_key_bytes)
        self._address: str = public_key_to_address(pub_key_bytes)
        self._scriptcode: bytes = (OP_DUP + OP_HASH160 + OP_PUSH_20 + address_to_public_key_hash(self.address) + OP_EQUALVERIFY + OP_CHECKSIG)
        self._unspents = []
        self._transactions = []

    @property
    def public_key(self):
        return self.public_key

    @property
    def address(self):
        return self._address

    @property
    def scriptcode(self):
        return self._scriptcode

    @property
    def balance(self):
        return sum(unspent.amount for unspent in self._unspents)

    @property
    def unspents(self):
        return self._unspents

    @property
    def transactions(self):
        return self._transactions

    def refresh_unspents(self):
        self._unspents = NETWORK_API.get_unspents(self._address)

    def refresh_transactions(self):
        self._transactions = NETWORK_API.get_transactions(self._address)
