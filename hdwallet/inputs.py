from enum import Enum
import re

from hdwallet.bips.bip_0039.words import BIP39_WORDS_EN


def is_valid_mnemonic(string):
    word_list = string.split()
    if len(word_list) == 12 or len(word_list) == 24:
        for word in word_list:
            if word not in BIP39_WORDS_EN:
                return False
        else:
            return True
    else:
        return False


class Inputs(Enum):
    XPUB = re.compile(r"xpub.+").fullmatch, "https://river.com/learn/terms/x/xpub-extended-public-key/"
    XPRV = re.compile(r"xprv.+").fullmatch, "https://river.com/learn/terms/x/xprv-extended-private-key/"
    SEED = re.compile(r"([0123456789abcdef][0123456789abcdef]){64,}").fullmatch, "https://river.com/learn/terms/s/seed-bitcoin/"
    MNEMONIC = is_valid_mnemonic, "https://river.com/learn/terms/m/mnemonic/"
    PATH = re.compile(r"m(/\d+'?)+").fullmatch, "https://river.com/learn/terms/d/derivation-path/"
    AMOUNT = re.compile(r"\d+").fullmatch, ""

    def __init__(self, criterion, reference):
        self._criterion = criterion
        self._reference = reference

    @property
    def criterion(self):
        return self._criterion

    @property
    def reference(self):
        return self._reference


RECOVER_TYPES = (
    Inputs.XPUB,
    Inputs.XPRV,
    Inputs.SEED,
    Inputs.MNEMONIC
)
