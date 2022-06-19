import os


BIP39_WORDS_EN = set()

with open(f"{os.path.dirname(__file__)}/words/english.txt", "r") as words:
    for line in words:
        BIP39_WORDS_EN.add(line.strip())


if __name__ == "__main__":
    print(os.path.dirname(__file__))
