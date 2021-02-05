"""
Module holding the classes for the manipulation of sound changes.
"""

from typing import Union

from maniphono import parse_segment, Sound, SoundSegment


class Token:
    def __init__(self):
        self.type = None

    def __str__(self) -> str:
        raise ValueError("Not implemented")

    def __repr__(self) -> str:
        return f"{self.type}:{str(self)}"

    def __hash__(self):
        raise ValueError("Not implemented")

    def __eq__(self, other) -> bool:
        raise ValueError("Not implemented")

    def __ne__(self, other) -> bool:
        raise ValueError("Not implemented")


class BoundaryToken(Token):
    def __init__(self):
        super().__init__()
        self.type = "boundary"

    def __str__(self) -> str:
        return "#"

    def __hash__(self):
        # TODO: all boundaries are equal here, but we should differentiate ^ and $
        return 1


class FocusToken(Token):
    def __init__(self):
        super().__init__()
        self.type = "focus"

    def __str__(self) -> str:
        return "_"


class EmptyToken(Token):
    def __init__(self):
        super().__init__()
        self.type = "empty"

    def __str__(self) -> str:
        return ":null:"


class BackRefToken(Token):
    def __init__(self, index: int, modifier=None):
        super().__init__()
        self.type = "backref"

        self.index = index
        self.modifier = modifier

    def __str__(self) -> str:
        if self.modifier:
            return f"@{self.index}[{self.modifier}]"

        return f"@{self.index}"

    def __add__(self, other):
        return BackRefToken(self.index + other, self.modifier)

    def __hash__(self):
        return hash(tuple(self.index, self.modifier))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other) -> bool:
        return hash(self) != hash(other)


class ChoiceToken(Token):
    def __init__(self, choices):
        self.choices = choices
        self.type = "choice"

    def __str__(self) -> str:
        return "|".join([str(choice) for choice in self.choices])

    def __hash__(self):
        return hash(tuple(self.choices))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __nq__(self, other) -> bool:
        return hash(self) != hash(other)


class Set(Token):
    def __init__(self, choices):
        super().__init__()
        self.choices = choices
        self.type = "set"

    def __str__(self) -> str:
        return "{" + "|".join([str(choice) for choice in self.choices]) + "}"

    def __hash__(self):
        return hash(tuple(self.choices))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other) -> bool:
        return hash(self) != hash(other)


# named segment token to distinguish from the maniphono SoundSegment
class SegmentToken(Token):
    def __init__(self, segment: Union[str, SoundSegment]):
        super().__init__()
        self.type = "segment"

        if isinstance(segment, str):
            self.segment = parse_segment(segment)
        else:
            self.segment = segment

    def __str__(self) -> str:
        return str(self.segment)

    def __hash__(self):
        return hash(self.segment)

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other) -> bool:
        return hash(self) == hash(other)

    def add_modifier(self, modifier):
        # TODO: properly implement with the __add__ operation from maniphono
        # hack using graphemic representation...
        grapheme = str(self.segment.sounds[0])
        sound = Sound(grapheme) + modifier
        segment = SoundSegment(sound)
        self.segment = segment
