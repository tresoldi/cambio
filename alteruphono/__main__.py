#!/usr/bin/env python3
# encoding: utf-8

"""
Entry point for the command line `alteruphono` utility.
"""

# Import Python standard libraries
import random

# Import 3rd party libraries
from pyclts import TranscriptionSystem

# Import our library
import alteruphono


def main():
    # import enki
    # import csv
    # import random

    # import yvyra
    # import os.path

    # TODO: write a reader
    rules = alteruphono.utils.read_sound_changes()
    bipa = TranscriptionSystem("bipa")
    sclasses = alteruphono.utils.read_sound_classes()
    features = alteruphono.utils.read_features()

    # param = {}
    # vocab = tuple(enki.random_words(10, param))
    vocab = ("m a m a", "p e p e", "d i t i")

    for i in range(100):
        rule = random.choice(rules)

        new_vocab = tuple(
            [
                alteruphono.apply_rule(word, rule, bipa, sclasses, features)
                for word in vocab
                # from alteruphono.sound_changer import apply_rule
            ]
        )

        if vocab != new_vocab:
            print(i, rule)
            print("==", vocab)
            print("==", new_vocab)
            print()


if __name__ == "__main__":
    main()
