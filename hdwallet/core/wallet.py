import itertools
from typing import Dict

from bip32utils import BIP32Key, BIP32_HARDEN
from mnemonic import Mnemonic

from hdwallet.configs import DERIVATION_ADDRESS_NUMBER
from hdwallet.core.key import Key
from hdwallet.core.utils import multithreading_execute


MNEMO = Mnemonic("english")


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
    def is_watch_wallet(self):
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

    @classmethod
    def from_xpub(cls, valid_xpub: str):
        return cls(BIP32Key.fromExtendedKey(valid_xpub, public=True))

    @classmethod
    def from_xprv(cls, valid_xprv: str):
        return cls(BIP32Key.fromExtendedKey(valid_xprv, public=False))

    @classmethod
    def from_seed(cls, valid_seed: bytes, valid_path: str):
        root_key = BIP32Key.fromEntropy(valid_seed)

        deriving_key = root_key
        index_list = valid_path.split('/')
        index_list.pop(0)  # pop m
        while index_list:
            _index = index_list.pop(0)
            if _index[-1] == "'":
                index = int(_index[:-1]) + BIP32_HARDEN
            else:
                index = int(_index)
            deriving_key = deriving_key.ChildKey(index)
        return cls(deriving_key)

    @classmethod
    def from_mnemonic(cls, valid_mnemonic_words: str, valid_passphrase: str, valid_path: str):
        seed = MNEMO.to_seed(mnemonic=valid_mnemonic_words, passphrase=valid_passphrase)
        return cls.from_seed(seed, valid_path)

    def refresh_transactions(self):
        multithreading_execute([key.refresh_transactions for key in self.__all_keys])

    def refresh_unspents(self):
        multithreading_execute([key.refresh_unspents for key in self.__all_keys])
