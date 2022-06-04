import re
from typing import Union

from bip32utils import BIP32Key, BIP32_HARDEN
from mnemonic import Mnemonic

from hdwallet.configs import DERIVATION_ADDRESS_NUMBER
from hdwallet.private_key import PrvKey
from hdwallet.public_key import PubKey

MNEMO = Mnemonic("english")


VALID_SEED_HEX = re.compile(r"([0123456789abcdef][0123456789abcdef]){64,}", re.I)
VALID_DERIVATION_PATH = re.compile(r"m(/\d+'?)+")
XPRV = re.compile(r"xprv.+")
XPUB = re.compile(r"xpub.+")


class WalletFSM:
    """
    The Business logic of this program is actually a finite state machine.
    """

    def __init__(self):
        self._current = self._start
        self.__master_key: Union[BIP32Key, None] = None
        self.__receive_keys = None
        self.__change_keys = None

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
        mnemonic_words = self.__ask_for(
            standard_query="Please input your BIP39 mnemonic words: \n",
            error_warning="Invalid word list, please enter again: \n",
            criterion=lambda s: True
        )
        passphrase = self.__ask_for(
            standard_query="Please input your passphrase: \n",
            error_warning="",
            criterion=lambda s: True
        )
        seed = MNEMO.to_seed(mnemonic=mnemonic_words, passphrase=passphrase)
        root_key = BIP32Key.fromEntropy(seed)
        path = self.__ask_for_path()
        master_private_key = self.__get_derivated_key(root_key, path)
        print("Wallet Created! ")
        self.__master_key = master_private_key
        self.__receive_keys, self.__change_keys = self.__generate_receive_change_key_chains()
        self._current = self._main_menu

    def _from_seed(self):
        root_key = BIP32Key.fromEntropy(
            bytes.fromhex(
                self.__ask_for(
                    standard_query="Please input your seed (in hex format): \n",
                    error_warning="Invalid seed, please enter again: \n",
                    criterion=VALID_SEED_HEX.fullmatch
                )
            )
        )
        path = self.__ask_for_path()
        master_private_key = self.__get_derivated_key(root_key, path)
        print("Wallet Created! ")
        self.__master_key = master_private_key
        self.__receive_keys, self.__change_keys = self.__generate_receive_change_key_chains()
        self._current = self._main_menu

    def _from_xprv(self):
        master_private_key = BIP32Key.fromExtendedKey(
            xkey=self.__ask_for(
                standard_query="Please input your extended private key (starts with xprv): \n",
                error_warning="Invalid xprv, please enter again: \n",
                criterion=XPRV.fullmatch
            ),
            public=False
        )
        print("Wallet Created! ")
        self.__master_key = master_private_key
        self.__receive_keys, self.__change_keys = self.__generate_receive_change_key_chains()
        self._current = self._main_menu

    def _from_xpub(self):
        master_public_key = BIP32Key.fromExtendedKey(
            xkey=self.__ask_for(
                standard_query="Please input your extended public key (starts with xpub): \n",
                error_warning="Invalid xpub, please enter again: \n",
                criterion=XPUB.fullmatch
            ),
            public=True
        )
        print("Wallet Created! ")
        self.__master_key = master_public_key
        self.__receive_keys, self.__change_keys = self.__generate_receive_change_key_chains()
        self._current = self._main_menu

    def _main_menu(self):
        print(
            "Enter 1 to get xprv \n"
            "Enter 2 to get xpub \n"
            "Enter 3 to get addresses and balance \n"
            "Enter 4 to refresh balances \n"
            "Enter 5 to send bitcoins \n"
            "Enter 0 to go back"
        )
        choices = {
            "1": self._get_xprv,
            "2": self._get_xpub,
            "3": self._get_addresses_and_balances,
            "4": self._refresh_balance,
            "5": self._send,
            "0": self._start
        }
        choice = input()
        while choice not in choices:
            choice = input("invalid choice, please enter again: \n")
        self._current = choices[choice]

    def _get_xprv(self):
        # todo: warning
        print("Your extended private key is: ")
        print(self.__master_key.ExtendedKey(private=True))
        input("Press any key to return\n")
        self._current = self._main_menu

    def _get_xpub(self):
        print("Your extended public key is: ")
        print(self.__master_key.ExtendedKey(private=False))
        input("Press any key to return\n")
        self._current = self._main_menu

    def _get_addresses_and_balances(self):
        print("Receive addresses: ")
        for key in self.__receive_keys:
            print(key.address, key.balance)
        print("Change addresses: ")
        for key in self.__change_keys:
            print(key.address, key.balance)
        input("Press any key to return\n")
        self._current = self._main_menu

    def _send(self):
        pass

    def _refresh_balance(self):
        for key in self.__receive_keys:
            key.refresh_unspents()
        for key in self.__change_keys:
            key.refresh_unspents()
        print("Refresh finished. ")
        self._current = self._main_menu

    def _sign(self):
        pass

    def _verify(self):
        pass

    def __generate_receive_change_key_chains(self):
        chains = []
        for i in range(2):
            key_chain = []
            derived_key = self.__master_key.ChildKey(i)
            for j in range(DERIVATION_ADDRESS_NUMBER):
                child_key = derived_key.ChildKey(j)
                if child_key.public:
                    pub = child_key.PublicKey()
                    pub_key = PubKey(pub)
                    key_chain.append(pub_key)
                else:
                    prv = child_key.PrivateKey()
                    prv_key = PrvKey(prv)
                    key_chain.append(prv_key)
            chains.append(key_chain)
        return chains

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

    @staticmethod
    def __ask_for(standard_query: str, error_warning: str, criterion):
        answer = input(standard_query)
        while not criterion(answer):
            answer = input(error_warning)
        return answer

    @staticmethod
    def __ask_for_path():
        # todo: add default to improve convenience
        return WalletFSM.__ask_for(
            standard_query="Please input the BIP32 derivation path: \n",
            error_warning="Invalid derivation path, please enter again: \n",
            criterion=VALID_DERIVATION_PATH.fullmatch
        )
