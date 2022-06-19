import itertools
from typing import Dict

from bip32utils import BIP32Key, BIP32_HARDEN

from hdwallet.configs import DERIVATION_ADDRESS_NUMBER
from hdwallet.core.key import Key
from hdwallet.core.utils import multithreading_execute


class Wallet:

    def __init__(self, master_key: BIP32Key):
        self.__master_key: BIP32Key = master_key
        self.__receive_keys: Dict[str, Key] = {}
        self.__change_keys: Dict[str, Key] = {}
        for i, key_chain in enumerate([self.__receive_keys, self.__change_keys]):
            derived_key = self.__master_key.ChildKey(i)
            for j in range(DERIVATION_ADDRESS_NUMBER):
                child_key = derived_key.ChildKey(j)
                if child_key.public:
                    pub_key_bytes = child_key.PublicKey()
                    key_chain[child_key.Address()] = Key(pub_key_bytes, is_public=True)
                else:
                    prv_key_bytes = child_key.PrivateKey()
                    key_chain[child_key.Address()] = Key(prv_key_bytes, is_public=False)

    def __getitem__(self, addr) -> Key:
        if key := self.__receive_keys.get(addr):
            return key
        if key := self.__change_keys.get(addr):
            return key
        raise KeyError

    @property
    def is_private(self):
        return not self.__master_key.public

    @property
    def is_public(self):
        return self.__master_key.public

    @property
    def xprv(self):
        return self.__master_key.ExtendedKey(private=True)

    @property
    def xpub(self):
        return self.__master_key.ExtendedKey(private=False)

    @property
    def receive_keys(self):
        return self.__receive_keys

    @property
    def change_keys(self):
        return self.__change_keys

    @property
    def __all_keys(self):
        return itertools.chain(self.__receive_keys.values(), self.__change_keys.values())

    @property
    def transactions(self):
        return sum([key.transactions for key in self.__all_keys], [])

    @property
    def unspents(self):
        return sum([key.unspents for key in self.__all_keys], [])

    @staticmethod
    def get_derivated_key(root: BIP32Key, path):
        key: BIP32Key = root
        path = path.split('/')
        path.pop(0)  # m
        while path:
            _index = path.pop(0)
            if _index[-1] == "'":
                index = int(_index[:-1]) + BIP32_HARDEN
            else:
                index = int(_index)
            key = key.ChildKey(index)
        return key

    def refresh_transactions(self):
        multithreading_execute([key.refresh_transactions for key in self.__all_keys])

    def refresh_unspents(self):
        multithreading_execute([key.refresh_unspents for key in self.__all_keys])
