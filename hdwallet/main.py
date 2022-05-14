from hdwallet.wallet import WalletFSM


def main():
    fsm = WalletFSM()
    while fsm.current:
        fsm.run()
