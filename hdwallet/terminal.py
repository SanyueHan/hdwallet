from typing import Union

from hdwallet.core.wallet import Wallet
from hdwallet.inputs import Inputs


class TerminalFSM:
    """
    The interaction program (Finite State Machine) between User and Wallet in terminal
    """

    def __init__(self):
        self._current = self._start
        self._wallet: Union[Wallet, None] = None

    @property
    def current(self):
        return self._current

    def run(self):
        self._current()

    def _start(self):
        self._wallet = None
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
        valid_mnemonic_words = self.__ask_for(
            standard_query="Please input your BIP39 mnemonic words: \n",
            error_warning="Invalid word list, please enter again: \n",
            criterion=lambda s: True
        )
        valid_passphrase = self.__ask_for(
            standard_query="Please input your passphrase: \n",
            error_warning="",
            criterion=lambda s: True
        )
        valid_path = self.__ask_for_path()
        self._wallet = Wallet.from_mnemonic(valid_mnemonic_words, valid_passphrase, valid_path)
        print("Wallet Created! ")
        self._current = self._main_menu

    def _from_seed(self):
        valid_seed = self.__ask_for(
            standard_query="Please input your seed (in hex format): \n",
            error_warning="Invalid seed, please enter again: \n",
            criterion=Inputs.SEED.criterion
        )
        valid_path = self.__ask_for_path()
        self._wallet = Wallet.from_seed(bytes.fromhex(valid_seed), valid_path)
        print("Wallet Created! ")
        self._current = self._main_menu

    def _from_xprv(self):
        valid_xprv = self.__ask_for(
            standard_query="Please input your extended private key (starts with xprv): \n",
            error_warning="Invalid xprv, please enter again: \n",
            criterion=Inputs.XPRV.criterion
        )
        self._wallet = Wallet.from_xprv(valid_xprv)
        print("Wallet Created! ")
        self._current = self._main_menu

    def _from_xpub(self):
        valid_xpub = self.__ask_for(
            standard_query="Please input your extended public key (starts with xpub): \n",
            error_warning="Invalid xpub, please enter again: \n",
            criterion=Inputs.XPUB.criterion
        )
        self._wallet = Wallet.from_xpub(valid_xpub)
        print("Wallet Created! ")
        self._current = self._main_menu

    def _main_menu(self):
        print("Enter 0 to go back")
        if self._wallet.is_private:
            print("Enter 1 to get xprv")
        print("Enter 2 to get xpub")
        print("Enter 3 to get transactions")
        print("Enter 4 to get unspent transactions")
        print("Enter 5 to get addresses and balances")
        print("Enter 6 to refresh transactions")
        print("Enter 7 to refresh unspent transactions")
        if self._wallet.is_private:
            print("Enter 8 to send bitcoins")
        choices = {
            "0": self._start,
            "2": self._get_xpub,
            "3": self._get_transactions,
            "4": self._get_unspents,
            "5": self._get_addresses_and_balances,
            "6": self._refresh_transactions,
            "7": self._refresh_unspents,
        }
        if self._wallet.is_private:
            choices["1"] = self._get_xprv
            choices["8"] = self._send
        choice = input()
        while choice not in choices:
            choice = input("invalid choice, please enter again: \n")
        self._current = choices[choice]

    def _get_xprv(self):
        # todo: warning and confirmation
        print("Your extended private key is: ")
        print(self._wallet.xprv)
        self.__press_any_key_to_return_to_main()

    def _get_xpub(self):
        print("Your extended public key is: ")
        print(self._wallet.xpub)
        self.__press_any_key_to_return_to_main()

    def _get_addresses_and_balances(self):
        print("Receive addresses: ")
        for addr, key in self._wallet.receive_keys.items():
            print(addr, key.balance)
        print("Change addresses: ")
        for addr, key in self._wallet.change_keys.items():
            print(addr, key.balance)
        self.__press_any_key_to_return_to_main()

    def _get_transactions(self):
        for tx in self._wallet.transactions:
            print(tx)
        self.__press_any_key_to_return_to_main()

    def _get_unspents(self):
        for usp in self._wallet.unspents:
            print(usp)
        self.__press_any_key_to_return_to_main()

    def _refresh_transactions(self):
        self._wallet.refresh_transactions()
        print("Transactions refreshed. ")
        self.__press_any_key_to_return_to_main()

    def _refresh_unspents(self):
        self._wallet.refresh_unspents()
        print("Unspents refreshed. ")
        self.__press_any_key_to_return_to_main()

    def _send(self):
        dst_addr = input("Please input the destination address: \n")
        src_addr = self.__ask_for(
            standard_query="Please input your source address \n",
            error_warning="This is not one of your address, please enter again: \n",
            criterion=lambda s: s in self._wallet.receive_keys or s in self._wallet.change_keys
        )
        if src_addr:
            self.__send_from(src_addr, dst_addr)
        # todo: support combination payment in the other branch
        # else:
        #     self.__send_to()
        self.__press_any_key_to_return_to_main()

    def __send_from(self, src, dst):
        key = self._wallet[src]
        amount = self.__ask_for(
            "Please input the amount to send \n",
            f"Insufficient funds, you could pay {key.balance} satoshi at most from this address. Please Enter again: \n",
            criterion=lambda a: int(a) < key.balance,
        )
        txid = key.send([(dst, amount, 'satoshi')])
        print(f"Successfully sent {amount} satoshi to {dst}, transaction id is: {txid}")

    def __send_to(self, dst):
        pass

    @staticmethod
    def __ask_for(standard_query: str, error_warning: str, criterion):
        answer = input(standard_query)
        while not criterion(answer):
            answer = input(error_warning)
        return answer

    @staticmethod
    def __ask_for_path():
        # todo: add default to improve convenience
        return TerminalFSM.__ask_for(
            standard_query="Please input the BIP32 derivation path: \n",
            error_warning="Invalid derivation path, please enter again: \n",
            criterion=Inputs.PATH.criterion
        )

    def __press_any_key_to_return_to_main(self):
        input("Press Enter to return\n")
        self._current = self._main_menu
