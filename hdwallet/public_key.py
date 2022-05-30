from bitsv.format import public_key_to_address
from coincurve import PublicKey

from hdwallet.network import NETWORK_API


class PubKey:
    def __init__(self, public_key: bytes):
        self._public_key = PublicKey(public_key)
        self._address = public_key_to_address(public_key)
        self._unspents = []
        self._transactions = []

    @property
    def address(self):
        return self._address

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
