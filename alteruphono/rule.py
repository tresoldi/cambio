"""
Module holding the `Rule` class.
"""


class Rule:
    """
    Basic rule class.

    The class serves mostly to carry at the same time the parsed `ante` and
    `post` ASTs along with the `source` rule, used for caching and hashing
    purposes.
    """

    def __init__(self, source, ast):
        self.source = source
        self.ante = ast["ante"]
        self.post = ast["post"]

    def __repr__(self):
        return repr(self.source)

    def __str__(self):
        return str(self.source)

    def __hash__(self):
        return hash(self.source)

    def __eq__(self, other):
        return self.source == other.source


def make_rule(rule_text, parser):
    """
    Parses a rule into a `Rule` object.

    Note that this function performs *no* normalization.
    """

    return Rule(rule_text, parser(rule_text))
