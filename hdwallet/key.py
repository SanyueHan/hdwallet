import json
import os
from typing import Union, List

from bitsv.format import public_key_to_address, address_to_public_key_hash
from bitsv.network.meta import Unspent
from bitsv.network.transaction import Transaction
from bitsv.transaction import OP_DUP, OP_HASH160, OP_PUSH_20, OP_EQUALVERIFY, OP_CHECKSIG, \
    calc_txid, create_p2pkh_transaction, sanitize_tx_data
from coincurve import PublicKey, PrivateKey

from hdwallet.configs import USP_CACHE_DIR
from hdwallet.errors import PubKeyUsedAsPrvKeyError
from hdwallet.network import NETWORK_API


def ensure_private(method):
    def method_with_check(self, *args, **kwargs):
        if self._prv_key:
            return method(self, *args, **kwargs)
        else:
            raise PubKeyUsedAsPrvKeyError
    return method_with_check


class Key:
    def __init__(self, key_bytes: bytes, is_public=False):
        self._prv_key: Union[PrivateKey, None]
        self._pub_key: PublicKey
        self._address: str
        if is_public:
            self._prv_key = None
            self._pub_key = PublicKey(key_bytes)
            self._address = public_key_to_address(key_bytes)
        else:
            self._prv_key = PrivateKey(key_bytes)
            self._pub_key = self._prv_key.public_key
            self._address = public_key_to_address(self._pub_key.format())
        self._scriptcode: bytes = (OP_DUP + OP_HASH160 + OP_PUSH_20 + address_to_public_key_hash(self.address) + OP_EQUALVERIFY + OP_CHECKSIG)
        self._transactions: List[Transaction] = self._load_transactions()
        self._unspents: List[Unspent] = self._load_unspents()

    @property
    def is_private(self):
        return self._prv_key is not None

    @property
    def is_public(self):
        return self._prv_key is None

    @property
    def public_key(self):
        # todo: temp inconsistent interface and return type for adaption with bitsv create_p2pkh_transaction function
        return self._pub_key.format()

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
        if self._unspents:
            self._dump_unspents()

    def refresh_transactions(self):
        self._transactions = [NETWORK_API.get_transaction(_id) for _id in NETWORK_API.get_transactions(self._address)]
        if self._transactions:
            self._dump_transactions()

    def verify(self, signature, data):
        """Verifies some data was signed by this private key.

        :param signature: The signature to verify.
        :type signature: ``bytes``
        :param data: The data that was supposedly signed.
        :type data: ``bytes``
        :rtype: ``bool``
        """
        return self._pub_key.verify(signature, data)

    @ensure_private
    def sign(self, data):
        """Signs some data which can be verified later by others using
        the public key.

        :param data: The message to sign.
        :type data: ``bytes``
        :returns: A signature compliant with BIP-62.
        :rtype: ``bytes``
        """
        return self._prv_key.sign(data)

    @ensure_private
    def send(self, outputs, fee=None, leftover=None, combine=True,
             message=None, unspents=None, custom_pushdata=False):  # pragma: no cover
        """Creates a signed P2PKH transaction and attempts to broadcast it on
        the blockchain. This accepts the same arguments as
        :func:`~bitsv.PrivateKey.create_transaction`.

        :param outputs: A sequence of outputs you wish to send in the form
                        ``(destination, amount, currency)``. The amount can
                        be either an int, float, or string as long as it is
                        a valid input to ``decimal.Decimal``. The currency
                        must be :ref:`supported <supported currencies>`.
        :type outputs: ``list`` of ``tuple``
        :param fee: The number of satoshi per byte to pay to miners. By default
                    BitSV will use a fee of `~bitsv.network.fees.DEFAULT_FEE_MEDIUM`.
        :type fee: ``float``
        :param leftover: The destination that will receive any change from the
                         transaction. By default BitSV will send any change to
                         the same address you sent from.
        :type leftover: ``str``
        :param combine: Whether or not BitSV should use all available UTXOs to
                        make future transactions smaller and therefore reduce
                        fees. By default BitSV will consolidate UTXOs.
        :type combine: ``bool``
        :param message: A message to include in the transaction. This will be
                        stored in the blockchain forever. Due to size limits,
                        each message will be stored in chunks of 100kb.
        :type message: ``str`` if custom_pushdata = False; ``list`` of ``tuple`` if custom_pushdata = True
        :param unspents: The UTXOs to use as the inputs. By default BitSV will
                         communicate with the blockchain itself.
        :type unspents: ``list`` of :class:`~bitsv.network.meta.Unspent`
        :param custom_pushdata: Adds control over push_data elements inside of the op_return by adding the
                                "custom_pushdata" = True / False parameter as a "switch" to the
                                :func:`~bitsv.PrivateKey.send` function and the
                                :func:`~bitsv.PrivateKey.create_transaction` functions.
        :type custom_pushdata: ``bool``
        :returns: The transaction ID.
        :rtype: ``str``
        """
        self.refresh_unspents()
        tx_hex = self._create_transaction(
            outputs, fee=fee, leftover=leftover, combine=combine,
            message=message, unspents=unspents, custom_pushdata=custom_pushdata
        )

        NETWORK_API.broadcast_tx(tx_hex)

        return calc_txid(tx_hex)

    def _create_transaction(self, outputs, fee=None, leftover=None, combine=True,
                            message=None, unspents=None, custom_pushdata=False):  # pragma: no cover
        """Creates a signed P2PKH transaction.

        :param outputs: A sequence of outputs you wish to send in the form
                        ``(destination, amount, currency)``. The amount can
                        be either an int, float, or string as long as it is
                        a valid input to ``decimal.Decimal``. The currency
                        must be :ref:`supported <supported currencies>`.
        :type outputs: ``list`` of ``tuple``
        :param fee: The number of satoshi per byte to pay to miners. By default
                    BitSV will use a fee of `~bitsv.network.fees.DEFAULT_FEE_MEDIUM`.
        :type fee: ``float``
        :param leftover: The destination that will receive any change from the
                         transaction. By default BitSV will send any change to
                         the same address you sent from.
        :type leftover: ``str``
        :param combine: Whether or not BitSV should use all available UTXOs to
                        make future transactions smaller and therefore reduce
                        fees. By default BitSV will consolidate UTXOs.
        :type combine: ``bool``
        :param message: A message to include in the transaction. This will be
                        stored in the blockchain forever. Due to size limits,
                        each message will be stored in chunks of 100kb.
        :type message: ``str`` if custom_pushdata = False; ``list`` of ``tuple`` if custom_pushdata = True
        :param unspents: The UTXOs to use as the inputs. By default BitSV will
                         communicate with the blockchain itself.
        :type unspents: ``list`` of :class:`~bitsv.network.meta.Unspent`
        :param custom_pushdata: Adds control over push_data elements inside of the op_return by adding the
                                "custom_pushdata" = True / False parameter as a "switch" to the
                                :func:`~bitsv.PrivateKey.send` function and the
                                :func:`~bitsv.PrivateKey.create_transaction` functions.
        :type custom_pushdata: ``bool``
        :returns: The signed transaction as hex.
        :rtype: ``str``
        """

        unspents, outputs = sanitize_tx_data(
            unspents or self.unspents,
            outputs,
            fee or 1,
            leftover or self.address,
            combine=combine,
            message=message,
            custom_pushdata=custom_pushdata
        )

        return create_p2pkh_transaction(self, unspents, outputs, custom_pushdata=custom_pushdata)

    def _load_transactions(self):
        return []

    def _dump_transactions(self):
        pass

    def _load_unspents(self):
        try:
            with open(USP_CACHE_DIR + self._address, "r") as usp_cache:
                return [Unspent.from_dict(usp_dict) for usp_dict in json.load(usp_cache)]
        except FileNotFoundError:
            return []

    def _dump_unspents(self):
        os.makedirs(USP_CACHE_DIR, exist_ok=True)
        with open(USP_CACHE_DIR + self._address, "w") as usp_cache:
            json.dump([usp.to_dict() for usp in self._unspents], fp=usp_cache, indent=4)
