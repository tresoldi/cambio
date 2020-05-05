# TODO: allow different boundary symbols, including "^" and "$"
# TODO: text normalization here as well
# TODO: add function to compare to string/list/tuple

"""
Sequence class.

This module defines a basic sequence class that allows to generalize
operations with sound sequences, taking care of details such as boundaries,
spaces, etc.
"""

# Import package
import alteruphono.utils


class Sequence:
    def __init__(self, sequence, sep=" "):
        # Split `sequence` string and convert to lists tuple ones
        if isinstance(sequence, str):
            sequence = sequence.split(sep)
        elif isinstance(sequence, tuple):
            sequence = list(sequence)

        # Make sure all entries are normalized
        sequence = [alteruphono.utils.clear_text(token) for token in sequence]

        # Add boundaries if necessary
        if sequence[0] != "#":
            sequence.insert(0, "#")
        if sequence[-1] != "#":
            sequence.append("#")

        # Store sequence and separator (used to return as str)
        self._sequence = sequence
        self._sep = sep

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
        return self._sep.join(self._sequence)

    # NOTE: not considering separator
    def __eq__(self, other):
        if len(self._sequence) != len(other._sequence):
            return False

        return all(
            [
                self_sound == other_sound
                for self_sound, other_sound in zip(
                    self._sequence, other._sequence
                )
            ]
        )
