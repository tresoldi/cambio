#!/usr/bin/env python3
# encoding: utf-8

# Import Python standard libraries
import random

# Import 3rd party libraries
from pyclts import TranscriptionSystem

# Import our library
import cambio

def main():
    #import enki
    #import csv
    #import random

    #import yvyra
    #import os.path

    # TODO: write a reader
    rules = cambio.utils.read_sound_changes()
    bipa = TranscriptionSystem("bipa")
    sclasses = cambio.utils.read_sound_classes()
    features = cambio.utils.read_features()

    #param = {}
    #vocab = tuple(enki.random_words(10, param))
    vocab = (
        "m a m a",
        "p e p e",
        "d i t i",
        )

    for i in range(100):
        rule = random.choice(rules)

        new_vocab = tuple(
            [cambio.apply_rule(word, rule, bipa, sclasses, features) for word in vocab]
        )

        if vocab != new_vocab:
            print(i, rule)
            print("==", vocab)
            print("==", new_vocab)
            print()

if __name__ == "__main__":
    main()
