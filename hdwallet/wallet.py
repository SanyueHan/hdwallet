import re
import itertools
from typing import Union, Dict

from bip32utils import BIP32Key, BIP32_HARDEN
from mnemonic import Mnemonic

from hdwallet.configs import DERIVATION_ADDRESS_NUMBER
from hdwallet.key import Key

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
        self.__receive_keys: Dict[str, Key] = {}
        self.__change_keys: Dict[str, Key] = {}

    @property
    def current(self):
        return self._current

    def run(self):
        self._current()

    @property
    def _all_keys(self):
        return itertools.chain(self.__receive_keys.values(), self.__change_keys.values())

    def _start(self):
        print(
            "Welcome to HDWallet!\n"
            "Enter 1 to generate wallet from mnemonic\n"
            "Enter 2 to generate wallet from a seed (in hex format)\n"
            "Enter 3 to generate wallet from extended private key\n"
            "Enter 4 to generate wallet from extended public key (create a watch wallet)\n"
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
        self.__generate_receive_change_keys()
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
        self.__generate_receive_change_keys()
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
        self.__generate_receive_change_keys()
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
        self.__generate_receive_change_keys()
        self._current = self._main_menu

    def _main_menu(self):
        print(
            "Enter 1 to get xprv\n"
            "Enter 2 to get xpub\n"
            "Enter 3 to get addresses and balance\n"
            "Enter 4 to get transactions\n"
            "Enter 5 to get utxos\n"
            "Enter 6 to receive bitcoins\n"
            "Enter 7 to send bitcoins\n"
            "Enter 0 to go back"
        )
        choices = {
            "1": self._get_xprv,
            "2": self._get_xpub,
            "3": self._get_addresses_and_balances,
            "4": self._get_transactions,
            "5": self._get_unspents,
            "6": self._receive,
            "7": self._send,
            "0": self._start
        }
        choice = input()
        while choice not in choices:
            choice = input("invalid choice, please enter again: \n")
        self._current = choices[choice]

    def _get_xprv(self):
        # todo: warning and confirmation
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
        self.__refresh_unspents()
        print("Receive addresses: ")
        for addr, key in self.__receive_keys.items():
            print(addr, key.balance)
        print("Change addresses: ")
        for addr, key in self.__change_keys.items():
            print(addr, key.balance)
        input("Press any key to return\n")
        self._current = self._main_menu

    def _get_transactions(self):
        self.__refresh_transactions()
        for key in self._all_keys:
            for tx in key.transactions:
                print(tx)
        input("Press any key to return\n")
        self._current = self._main_menu

    def _get_unspents(self):
        self.__refresh_unspents()
        for key in self._all_keys:
            for usp in key.unspents:
                print(usp)
        input("Press any key to return\n")
        self._current = self._main_menu

    def _receive(self):
        pass

    def _send(self):
        dst_addr = input("Please input the destination address: \n")
        src_addr = self.__ask_for(
            standard_query="Please input your source address \n",
            error_warning="This is not one of your address, please enter again: \n",
            criterion=lambda s: s in self.__receive_keys or s in self.__change_keys
        )
        if src_addr:
            self.__send_from(src_addr, dst_addr)
        # todo: support combination payment in the other branch
        # else:
        #     self.__send_to()
        input("Press any key to return\n")
        self._current = self._main_menu

    def _sign(self):
        pass

    def _verify(self):
        pass

    def __send_from(self, src, dst):
        key = self[src]
        amount = self.__ask_for(
            "Please input the amount to send \n",
            f"Insufficient funds, you could pay {key.balance} satoshi at most from this address",
            criterion=lambda a: True,
        )
        txid = key.send([(dst, amount, 'satoshi')])
        print(f"Successfully sent {amount} satoshi to {dst}, transaction id is: {txid}")

    def __send_to(self, dst):
        pass

    def __refresh_unspents(self):
        for key in self._all_keys:
            key.refresh_unspents()
        print("Unspents refreshed. ")

    def __refresh_transactions(self):
        for key in self._all_keys:
            key.refresh_transactions()
        print("Transactions refreshed. ")

    def __generate_receive_change_keys(self):
        for i, key_chain in enumerate([self.__receive_keys, self.__change_keys]):
            key_chain.clear()
            derived_key = self.__master_key.ChildKey(i)
            for j in range(DERIVATION_ADDRESS_NUMBER):
                child_key = derived_key.ChildKey(j)
                if child_key.public:
                    pub_key_bytes = child_key.PublicKey()
                    key_chain[child_key.Address()] = Key(pub_key_bytes, is_public=True)
                else:
                    prv_key_bytes = child_key.PrivateKey()
                    key_chain[child_key.Address()] = Key(prv_key_bytes, is_public=False)

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

    def __getitem__(self, addr) -> Key:
        if key := self.__receive_keys.get(addr):
            return key
        if key := self.__change_keys.get(addr):
            return key
        raise KeyError
