from hdwallet.terminal import TerminalFSM as Machine


def main():
    fsm = Machine()
    while fsm.current:
        fsm.run()
