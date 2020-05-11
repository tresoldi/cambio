"""
Module holding the `Sequence` class.

This module defines a basic sequence class that allows to generalize
operations with sound sequences, taking care of details such as boundaries,
spaces, etc.
"""

# Import Python standard libraries
import re
import unicodedata


class Sequence:
    """
    Basic class for sound classes.

    The class mostly takes care of splitting, normalization (which is
    optional), and boundaries. Internally, the sequence is stored as a tuple,
    so we have an immutable value.
    """

    def __init__(self, sequence, normalize=True):
        # Split `sequence` string and convert to lists tuple ones
        if isinstance(sequence, str):
            if normalize:
                sequence = re.sub(r"\s+", " ", sequence).strip()
                sequence = unicodedata.normalize("NFC", sequence)
            sequence = sequence.split(" ")
        elif isinstance(sequence, (tuple, list)):
            sequence = [
                unicodedata.normalize("NFC", token) if normalize else token
                for token in sequence
            ]

        # Add boundaries if necessary
        if sequence[0] != "#":
            sequence.insert(0, "#")
        if sequence[-1] != "#":
            sequence.append("#")

        # Store sequence and separator (used to return as str)
        self._sequence = tuple(sequence)

        # Initialize index for iteration
        self._iter_idx = None

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

    def __repr__(self):
        return repr(self._sequence)

    def __str__(self):
        return " ".join(self._sequence)

    # NOTE: this is the only rich comparison that accepts non-Sequence
    def __eq__(self, other):
        if not isinstance(other, Sequence):
            return self == Sequence(other)

        return self._sequence == other._sequence

    def __lt__(self, other):
        return self._sequence < other._sequence

    def __le__(self, other):
        return self._sequence <= other._sequence

    def __gt__(self, other):
        return self._sequence > other._sequence

    def __ge__(self, other):
        return self._sequence >= other._sequence

    def __hash__(self):
        return hash(self._sequence)
