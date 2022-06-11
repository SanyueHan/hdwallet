import os


DERIVATION_ADDRESS_NUMBER = int(os.environ.get("DERIVATION_ADDRESS_NUMBER", "10"))

TRX_CACHE_DIR = os.environ.get("TRX_CACHE_DIR", "cache/trx/")
USP_CACHE_DIR = os.environ.get("USP_CACHE_DIR", "cache/usp/")
