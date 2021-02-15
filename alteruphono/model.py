"""
Module holding the classes for the manipulation of sound changes.
"""

from typing import Union

from maniphono import parse_segment, Sound, SoundSegment

# TODO: all tokens should have a method to return a corresponding segment

class Token:
    def __init__(self):
        # TODO: applies only to back-ref or should we reuse if possible for set/choice?
        self.index = None

    def __str__(self) -> str:
        raise ValueError("Not implemented")

    def __hash__(self):
        raise ValueError("Not implemented")

    def __eq__(self, other) -> bool:
        raise ValueError("Not implemented")

    def __ne__(self, other) -> bool:
        raise ValueError("Not implemented")


class BoundaryToken(Token):
    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        return "#"

    def __repr__(self) -> str:
        return f"boundary_tok:{str(self)}"

    def __hash__(self) -> int:
        # TODO: all boundaries are equal here, but we should differentiate ^ and $
        return hash(1)


class FocusToken(Token):
    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        return "_"

    def __repr__(self) -> str:
        return f"focus_tok:{str(self)}"

    def __hash__(self) -> int:
        # TODO: all focus are equal here
        return hash(2)


class EmptyToken(Token):
    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        return ":null:"

    def __repr__(self) -> str:
        return f"empty_tok:{str(self)}"

    def __hash__(self) -> int:
        # TODO: all empty are equal here (but should they be?)
        return hash(3)


class BackRefToken(Token):
    def __init__(self, index: int, modifier=None):
        super().__init__()

        self.index = index
        self.modifier = modifier

    def __str__(self) -> str:
        if self.modifier:
            return f"@{self.index}[{self.modifier}]"

        return f"@{self.index}"

    def __repr__(self) -> str:
        return f"backref_tok:{str(self)}"

    def __add__(self, other):
        return BackRefToken(self.index + other, self.modifier)

    def __hash__(self):
        return hash(tuple([tuple(self.modifier), self.index]))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other) -> bool:
        return hash(self) != hash(other)


class ChoiceToken(Token):
    def __init__(self, choices):
        super().__init__()
        self.choices = choices

    def __str__(self) -> str:
        return "|".join([str(choice) for choice in self.choices])

    def __repr__(self) -> str:
        return f"choice_tok:{str(self)}"

    def __hash__(self):
        return hash(tuple(self.choices))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other) -> bool:
        return hash(self) != hash(other)


class SetToken(Token):
    def __init__(self, choices):
        super().__init__()
        self.choices = choices

    def __str__(self) -> str:
        return "{" + "|".join([str(choice) for choice in self.choices]) + "}"

    def __repr__(self) -> str:
        return f"set_tok:{str(self)}"

    def __hash__(self):
        return hash(tuple(self.choices))

    def __eq__(self, other) -> bool:
        return hash(self) == hash(other)

    def __ne__(self, other) -> bool:
        return hash(self) != hash(other)


# named segment token to distinguish from the maniphono SoundSegment
# TODO: rename `segment` argument
class SegmentToken(Token):
    def __init__(self, segment: Union[str, Sound, SoundSegment]):
        super().__init__()

        if isinstance(segment, str):
            self.segment = parse_segment(segment)
        elif isinstance(segment, Sound):
            self.segment = SoundSegment(segment)
        else:
            self.segment = segment

    def __str__(self) -> str:
        return str(self.segment)

    def __repr__(self) -> str:
        return f"segment_tok:{str(self)}"

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
