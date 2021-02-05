import re
import unicodedata
from typing import List, Tuple

from .model import Token, BoundaryToken, FocusToken, EmptyToken, BackRefToken, ChoiceToken, Set, SegmentToken

# TODO: context must have a focus

# Define capture regexes for rules without and with context
RE_RULE_NOCTX = re.compile(r"^(?P<ante>[^>]+)>(?P<post>[^/]+)$")
RE_RULE_CTX = re.compile(r"^(?P<ante>[^>]+)>(?P<post>[^/]+)/(?P<context>.+)$")
RE_BACKREF_NOMOD = re.compile(r"^@(?P<index>\d+)$")
RE_BACKREF_MOD = re.compile(r"^@(?P<index>\d+)\[(?P<mod>[^\]]+)\]$")


# TODO: __repr__, __str__, and __hash__ should deal with ante and post, not source
class Rule:
    def __init__(self, source: str):
        self.source = source
        self.ante, self.post = parse_rule(source)

    def __repr__(self) -> str:
        ante_str = " ".join([repr(token) for token in self.ante])
        post_str = " ".join([repr(token) for token in self.post])
        return "%s >>> %s" % (ante_str, post_str)

    def __str__(self) -> str:
        return str(self.source)

    def __hash__(self):
        return hash(self.source)

    def __eq__(self, other) -> bool:
        return self.source == other.source


def preprocess(rule: str) -> str:
    """
    Internal function for pre-processing of rules.

    @param rule: The rule to be preprocessed.
    @return: The cleaned, preprocessed rule.
    """

    # 1. Normalize to NFD, as per maniphono
    rule = unicodedata.normalize("NFD", rule)

    # 2. Replace multiple spaces with single ones, and remove leading/trailing spaces
    rule = re.sub(r"\s+", " ", rule.strip())

    return rule


def parse_atom(atom_str: str) -> Token:
    # Internal function for parsing an atom
    atom_str = atom_str.strip()

    if atom_str[0] == "{" and atom_str[-1] == "}":
        # a set
        # TODO: what if it is a set with modifiers?
        choices = [parse_atom(choice) for choice in atom_str[1:-1].split("|")]
        return Set(choices)
    elif "|" in atom_str:
        # If we have a choice, we parse it just like a sequence
        choices = [parse_atom(choice) for choice in atom_str.split("|")]
        return ChoiceToken(choices)
    elif atom_str == "#":
        return BoundaryToken()
    elif atom_str == "_":
        return FocusToken()
    elif atom_str == ":null:":
        return EmptyToken()
    elif (match := re.match(RE_BACKREF_MOD, atom_str)) is not None:
        # Return the index as an integer, along with any modifier.
        # Note that we substract one unit as our lists indexed from 1 (unlike Python,
        # which indexes from zero)
        # TODO: deal with modifiers
        mod = match.group("mod")
        index = int(match.group("index")) - 1
        return BackRefToken(index, mod)
    elif (match := re.match(RE_BACKREF_NOMOD, atom_str)) is not None:
        # Return the index as an integer.
        # Note that we substract one unit as our lists indexed from 1 (unlike Python,
        # which indexes from zero)
        index = int(match.group("index")) - 1
        return BackRefToken(index)

    # Assume it is a grapheme
    return SegmentToken(atom_str)


def parse_seq_as_rule(seq):
    seq = preprocess(seq)
    return [parse_atom(atom) for atom in seq.strip().split()]


def parse_rule(rule:str) -> Tuple[List[Token], List[Token]]:
    # Pre-process the rule and then split into `ante`, `post`, and `context`, which
    # are stripped of leading/trailing spaces. As features, feature values, and graphemes
    # cannot have the reserved ">" and "/" characters, this is very straightforward:
    # we just try to match both without and with context, and see if we get a match.
    # While a single regular expression could be used, splitting in two different ones
    # is better, also due to our usage of named captures (that must be unique in the
    # whole regular expression)
    rule = preprocess(rule)
    if (match := re.match(RE_RULE_CTX, rule)) is not None:
        ante, post, context = (
            match.group("ante"),
            match.group("post"),
            match.group("context"),
        )
    elif (match := re.match(RE_RULE_NOCTX, rule)) is not None:
        ante, post, context = match.group("ante"), match.group("post"), None
    else:
        raise ValueError("Unable to parse rule `rule`")

    # Strip ante, post and context
    ante_seq = [parse_atom(atom) for atom in ante.strip().split()]
    post_seq = [parse_atom(atom) for atom in post.strip().split()]

    # If there is a context, parse it, split in `left` and `right`, in terms of the
    # focus, and merge it to `ante` and `post` so that we return only these two seqs
    if context:
        cntx_seq = [parse_atom(atom) for atom in context.strip().split()]
        for idx, token in enumerate(cntx_seq):
            if token.type == "focus":
                left_seq, right_seq = cntx_seq[:idx], cntx_seq[idx + 1:]
                break

        # cache the length of the context left, of ante, and of post, used for
        # backreference offsets
        offset_left = len(left_seq)
        offset_ante = len(ante_seq)
        offset_post = len(post_seq)

        # Shift the backreferences indexes of 'ante' and 'post' by the length of the
        # left context (`p @2 / a _` --> `a p @3`)
        if left_seq:
            ante_seq = [
                token if token.type != "backref" else token + offset_left
                for token in ante_seq
            ]
            post_seq = [
                token if token.type != "backref" else token + offset_left
                for token in post_seq
            ]

        # It is easy to build the new `ante_seq`: we just join `left_seq` and
        # `ante_seq` (with the already updated backref indexes) and append all
        # items in 'right_seq` also shifting backref indexes if necessary
        ante_seq = left_seq + ante_seq
        ante_seq += [
            token if token.type != "backref" else token + offset_left + offset_ante
            for token in right_seq
        ]

        # Building the new `post_seq` is a bit more cmplex, as we need to apply the
        # offset and replace all literals so as to refer to ante (so that, for
        # example, in "V s -> @1 z @1 / # p|b r _ t|d" we will get
        # becomes "@1 @2 @3 @4 z @4 @6" as `post`.
        # Note that we replace with backrefences even literals, as they might match
        # more than one actual sound: for example, if the literal is a class (i.e.,
        # an "incomplete sound"), such as C, it will much a number of consonants,
        # but we cannot know which one was matched unless we keep a backreference
        post_seq = [BackRefToken(i) for i, _ in enumerate(left_seq)] + post_seq
        post_seq += [
            BackRefToken(i + offset_left + offset_ante) for i, _ in enumerate(right_seq)
        ]

    return ante_seq, post_seq
