import itertools
from typing import Dict

from bip_utils import Bip32Secp256k1
from mnemonic import Mnemonic

from hdwallet.configs import DERIVATION_ADDRESS_NUMBER
from hdwallet.core.key import Key
from hdwallet.utils import multithreading_execute


MNEMO = Mnemonic("english")


class Wallet:

    def __init__(self, master_key: Bip32Secp256k1):
        self.__master_key: Bip32Secp256k1 = master_key
        self.__receive_keys: Dict[str, Key] = {}
        self.__change_keys: Dict[str, Key] = {}
        for i, key_chain in enumerate([self.__receive_keys, self.__change_keys]):
            derived_key = self.__master_key.ChildKey(i)
            for j in range(DERIVATION_ADDRESS_NUMBER):
                child_key = derived_key.ChildKey(j)
                if child_key.IsPublicOnly():
                    pub_key_bytes = child_key.PublicKey().RawCompressed().m_data_bytes
                    pub_key = Key(pub_key_bytes, is_public=True)
                    key_chain[pub_key.address] = pub_key
                else:
                    prv_key_bytes = child_key.PrivateKey().Raw().m_data_bytes
                    prv_key = Key(prv_key_bytes, is_public=False)
                    key_chain[prv_key.address] = prv_key

    @property
    def is_watch_wallet(self):
        return self.__master_key.IsPublicOnly()

    @property
    def xprv(self):
        return self.__master_key.PrivateKey().ToExtended()

    @property
    def xpub(self):
        return self.__master_key.PublicKey().ToExtended()

    @property
    def receive_addresses(self):
        return self.__receive_keys.keys()

    @property
    def receive_addresses_and_balances(self):
        return ((addr, key.balance) for addr, key in self.__receive_keys.items())

    @property
    def change_addresses(self):
        return self.__change_keys.keys()

    @property
    def change_addresses_and_balances(self):
        return ((addr, key.balance) for addr, key in self.__change_keys.items())

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
        return cls(Bip32Secp256k1.FromExtendedKey(valid_xpub))

    @classmethod
    def from_xprv(cls, valid_xprv: str):
        return cls(Bip32Secp256k1.FromExtendedKey(valid_xprv))

    @classmethod
    def from_seed(cls, valid_seed: bytes, valid_path: str):
        return cls(Bip32Secp256k1.FromSeedAndPath(valid_seed, valid_path))

    @classmethod
    def from_mnemonic(cls, valid_mnemonic_words: str, valid_passphrase: str, valid_path: str):
        seed = MNEMO.to_seed(mnemonic=valid_mnemonic_words, passphrase=valid_passphrase)
        return cls.from_seed(seed, valid_path)

    def refresh_transactions(self):
        multithreading_execute([key.refresh_transactions for key in self.__all_keys])

    def refresh_unspents(self):
        multithreading_execute([key.refresh_unspents for key in self.__all_keys])

    def simple_send(self, src, dst, amount) -> str:
        if key := self.__receive_keys.get(src, self.__change_keys.get(src)):
            return key.send([(dst, amount, 'satoshi')])
        else:
            raise KeyError(f"No corresponding key found for address: {src}")
