"""
Class definitions for AST elements.

These elements were first defined, when prototyping the library, as plain
Python dictionaries, a structure that is likely still visible. The
decision to move to a proper class-based system was motivated by
the clean code it allows, including for documentation and for academic
report.
"""

# TODO: add __str__ and __repr__
class Features:
    def __init__(self, positive, negative, custom=None):
        self.positive = positive
        self.negative = negative
        if not custom:
            self.custom = {}
        else:
            self.custom = custom

    def __eq__(self, other):
        if tuple(sorted(self.positive)) != tuple(sorted(other.positive)):
            return False

        if tuple(sorted(self.negative)) != tuple(sorted(other.negative)):
            return False

        return self.custom == other.custom


class Token:
    def __init__(self):
        pass

    def __contains__(self, key):
        return key in self.__dict__

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class TokenFocus(Token):
    toktype = "focus"

    def __init__(self, symbol="_"):
        super().__init__()
        self.symbol = symbol


class TokenNull(Token):
    toktype = "null"

    def __init__(self):
        super().__init__()


class TokenBoundary(Token):
    toktype = "boundary"

    def __init__(self, symbol="#"):
        super().__init__()
        self.symbol = symbol


class TokenSylBreak(Token):
    toktype = "sylbreak"

    def __init__(self, symbol="."):
        super().__init__()
        self.symbol = symbol


class TokenIPA(Token):
    toktype = "ipa"

    def __init__(self, grapheme, modifier=None):
        super().__init__()
        self.ipa = grapheme
        self.modifier = modifier


class TokenSoundClass(Token):
    toktype = "sound_class"

    def __init__(self, sound_class, modifier=None):
        super().__init__()
        self.sound_class = sound_class
        self.modifier = modifier


class TokenBackRef(Token):
    toktype = "backref"

    def __init__(self, index, modifier=None, correspondence=None):
        super().__init__()
        self.index = index
        self.modifier = modifier
        self.correspondence = correspondence


class TokenAlternative(Token):
    toktype = "alternative"

    def __init__(self, alternative, modifier=None):
        super().__init__()
        self.alternative = alternative
        self.modifier = modifier

    def __str__(self):
        tmp = copy(self.__dict__)
        tmp.pop("alternative")
        return "|".join([str(tok) for tok in self.alternative]) + str(tmp)

    def __eq__(self, other):
        if other.toktype != "alternative":
            return False

        if self.modifier != other.modifier:
            return False

        if len(self.alternative) != len(other.alternative):
            return False

        for self_alt, other_alt in zip(self.alternative, other.alternative):
            if self_alt != other_alt:
                return False

        return True
