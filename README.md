
# hdwallet
```
Licence: MIT Licence
Authur: Han Sanyue
Contact: 
Language: Python (>=3.8)
HomePage: 
```

## [Introduction](https://river.com/learn/terms/h/hd-wallet/)
A Hierarchical Deterministic (HD) wallet is the term used to describe a wallet which uses a seed to derive public and private keys. HD wallets were implemented as a Bitcoin standard with BIP 32. Before this, most wallets generated unrelated keys each time a user required a new address. This format, called a Just-a-Bunch-of-Keys (JBOK) wallet, required the wallet to backup each key individually, a significant inconvenience for both wallets and users. HD wallets can be backed up by storing a single seed of 64 bytes.

## Getting Started on Windows/Linux/macOS
```shell
pip3 install --user -r requirements.txt
```

```shell
python3 hdwallet.py
```