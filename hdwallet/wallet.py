import re
from typing import Union

from bip32utils import BIP32Key, BIP32_HARDEN

VALID_DERIVATION_PATH = re.compile(r"m(/\d+'?)+")


class WalletFSM:
    """
    The Business logic of this program is actually a finite state machine.
    """
    ADDRESS_DISPLAY_LIMIT = 10

    def __init__(self):
        self._key: Union[BIP32Key, None] = None
        self._current = self._start

    @property
    def current(self):
        return self._current

    def run(self):
        self._current()

    def _start(self):
        print(
            "Welcome to HDWallet! \n"
            "Enter 1 to generate wallet from mnemonic \n"
            "Enter 2 to generate wallet from a seed (in hex format) \n"
            "Enter 3 to generate wallet from extended private key \n"
            "Enter 4 to generate wallet from extended public key (create a watch wallet) \n"
            "Enter 0 to exit"
        )
        choices = {
            '1': self._from_mnemonic,
            '2': self._from_seed,
            '3': self._from_xprv,
            '4': self._from_xpub,
            '0': None
        }
        choice = input()
        while choice not in choices:
            choice = input("invalid choice, please enter again: \n")
        self._current = choices[choice]

    def _from_mnemonic(self):
        pass

    def _from_seed(self):
        root_key = None
        while not root_key:
            try:
                seed = bytes.fromhex(input("Please input your seed (in hex format): \n"))
                root_key = BIP32Key.fromEntropy(seed)
            except ValueError as ve:
                print(ve)
        path = input("Please input the BIP32 derivation path: \n")
        # todo: add default to improve convenience
        while not VALID_DERIVATION_PATH.fullmatch(path):
            path = input("Invalid derivation path, please enter again: \n")
        master_private_key = self.__get_derivated_key(root_key, path)
        print("Wallet Created! ")
        self._key = master_private_key
        self._current = self._main_menu

    def _from_xprv(self):
        pass

    def _from_xpub(self):
        pass

    def _main_menu(self):
        print(
            "Enter 1 to get xprv \n"
            "Enter 2 to get xpub \n"
            "Enter 3 to get addresses and balance \n"
            "Enter 4 to send bitcoins \n"
            "Enter 0 to go back"
        )
        choices = {
            "1": self._get_xprv,
            "2": self._get_xpub,
            "3": self._get_addresses_and_balances,
            "4": self._send,
            "0": self._start
        }
        choice = input()
        while choice not in choices:
            choice = input("invalid choice, please enter again: \n")
        self._current = choices[choice]

    def _get_xprv(self):
        # todo: warning
        print("Your extended private key is: ")
        print(self._key.ExtendedKey(private=True))
        input("Press any key to return. ")
        self._current = self._main_menu

    def _get_xpub(self):
        print("Your extended public key is: ")
        print(self._key.ExtendedKey(private=False))
        input("Press any key to return. ")
        self._current = self._main_menu

    def _get_addresses_and_balances(self):
        pass

    def _send(self):
        pass

    def _sign(self):
        pass

    def _verify(self):
        pass

    @staticmethod
    def __get_derivated_key(root: BIP32Key, path):
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
