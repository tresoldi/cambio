# TODO: allow different boundary symbols, including "^" and "$"
# TODO: text normalization here as well
# TODO: add function to compare to string/list/tuple

"""
Sequence class.

This module defines a basic sequence class that allows to generalize
operations with sound sequences, taking care of details such as boundaries,
spaces, etc.
"""

# Import Python standard libraries
import re
import unicodedata

# Import package
import alteruphono.utils

# TODO: drop this object and only use a controlled tuple? add an __hash__?
#       or store internally as a tuple?
# TODO: should have a sorting method
# TODO: optional normalizatio
class Sequence:
    def __init__(self, sequence):
        # Split `sequence` string and convert to lists tuple ones
        if isinstance(sequence, str):
            sequence = re.sub(r"\s+", " ", sequence).strip()
            sequence = unicodedata.normalize("NFC", sequence)
            sequence = sequence.split(" ")
        elif isinstance(sequence, (tuple, list)):
            sequence = [unicodedata.normalize("NFC", token) for
            token in sequence]

        # Add boundaries if necessary
        if sequence[0] != "#":
            sequence.insert(0, "#")
        if sequence[-1] != "#":
            sequence.append("#")

        # Store sequence and separator (used to return as str)
        self._sequence = tuple(sequence)

    def __getitem__(self, idx):
        return self._sequence[idx]

    def __iter__(self):
        self._iter_idx = 0
        return self

    def __next__(self):
        if self._iter_idx == len(self._sequence):
            raise StopIteration

        ret = self._sequence[self._iter_idx]
        self._iter_idx += 1

        return ret

    def __len__(self):
        return len(self._sequence)

    # TODO: __repr__ and __str__ can be stored (as immutable)? do we need it?
    def __repr__(self):
        return repr(self._sequence)

    def __str__(self):
        return " ".join(self._sequence)

    # TODO: should take part of the work of `check_match`?
    def __eq__(self, other):
        if not isinstance(other, Sequence):
            return self == Sequence(other)

        return self._sequence == other._sequence

    def __hash__(self):
        return hash(self._sequence)
