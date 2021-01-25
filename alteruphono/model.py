"""
Module holding the classes for the manipulation of sound changes.
"""

import maniphono


class Token:
    def __init__(self):
        self.type = None

    def __str__(self):
        raise ValueError("Not implemented")

    def __repr__(self):
        return f"{self.type}:{str(self)}"

    def __hash__(self):
        raise ValueError("Not implemented")

    def __eq__(self, other):
        raise ValueError("Not implemented")

    def __ne__(self, other):
        raise ValueError("Not implemented")


class Boundary(Token):
    def __init__(self):
        self.type = "boundary"

    def __str__(self):
        return "#"

    def __hash__(self):
        # TODO: all boundaries are equal here, but we should differentiate ^ and $
        return 1


class Focus(Token):
    def __init__(self):
        self.type = "focus"

    def __str__(self):
        return "_"


class Empty(Token):
    def __init__(self):
        self.type = "empty"

    def __str__(self):
        return ":null:"


class BackRef(Token):
    def __init__(self, index, modifier=None):
        self.type = "backref"

        self.index = index
        self.modifier = modifier

    def __str__(self):
        if self.modifier:
            return f"@{self.index}[{self.modifier}]"

        return f"@{self.index}"

    def __add__(self, value):
        return BackRef(self.index + value, self.modifier)

    def __hash__(self):
        return hash(tuple(self.index, self.modifier))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return hash(self) != hash(other)


class Choice(Token):
    def __init__(self, choices):
        self.choices = choices
        self.type = "choice"

    def __str__(self):
        return "|".join([str(choice) for choice in self.choices])

    def __hash__(self):
        return hash(tuple(self.choices))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __nq__(self, other):
        return hash(self) != hash(other)


class Set(Token):
    def __init__(self, choices):
        self.choices = choices
        self.type = "set"

    def __str__(self):
        return "{" + "|".join([str(choice) for choice in self.choices]) + "}"

    def __hash__(self):
        return hash(tuple(self.choices))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return hash(self) != hash(other)


# named segment token to distinguish from the maniphono SoundSegment
class SegmentToken(Token):
    def __init__(self, grapheme):
        self.segment = maniphono.parse_segment(grapheme)
        self.type = "segment"

    def __str__(self):
        return str(self.segment)

    def __hash__(self):
        return hash(self.segment)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return hash(self) == hash(other)
