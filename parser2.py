# new, ongoing parser with regular expressions

import csv
import re
import unicodedata

import maniphono

# TODO: context must have a focus

# Define capture regexes for rules without and with context
RE_RULE_NOCTX = re.compile(r"^(?P<ante>[^>]+)>(?P<post>[^/]+)$")
RE_RULE_CTX = re.compile(r"^(?P<ante>[^>]+)>(?P<post>[^/]+)/(?P<context>.+)$")
RE_BACKREF_NOMOD = re.compile(r"^@(?P<index>\d+)$")
RE_BACKREF_MOD = re.compile(r"^@(?P<index>\d+)\[(?P<mod>[^\]]+)\]$")


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
        self.index = index
        self.modifier = modifier
        self.type = "backref"

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


# named segment token to distinguish from the maniphono Segment
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


def preprocess(rule):
    """
    Internal function for pre-processing of rules.
    """

    # 1. Normalize to NFD, as per maniphono
    rule = unicodedata.normalize("NFD", rule)

    # 2. Replace multiple spaces with single ones, and remove leading/trailing spaces
    rule = re.sub(r"\s+", " ", rule.strip())

    return rule


def parse_modifier(mod_str):
    modifiers = {"-": [], "+": []}

    # TODO: use splitter from maniphono
    for mod in mod_str.split(","):
        if mod[0] == "-":
            modifiers["-"].append(mod[1:])
        elif mod[0] == "+":
            modifiers["+"].append(mod[1:])
        else:
            modifiers["+"].append(mod)

    return modifiers


# an atom can be
# - a grapheme
# - a back reference
def parse_atom(atom_str):
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
        return Choice(choices)
    elif atom_str == "#":
        return Boundary()
    elif atom_str == "_":
        return Focus()
    elif atom_str == ":null:":
        return Empty()
    elif (match := re.match(RE_BACKREF_MOD, atom_str)) is not None:
        # Return the index as an integer, along with any modifier.
        # Note that we substract one unit as our lists indexed from 1 (unlike Python,
        # which indexes from zero)
        # TODO: deal with modifiers
        mod = parse_modifier(match.group("mod"))
        index = int(match.group("index")) - 1
        return BackRef(index, mod)
    elif (match := re.match(RE_BACKREF_NOMOD, atom_str)) is not None:
        # Return the index as an integer.
        # Note that we substract one unit as our lists indexed from 1 (unlike Python,
        # which indexes from zero)
        index = int(match.group("index")) - 1
        return BackRef(index)
    else:
        # assume it is a grapheme
        return SegmentToken(atom_str)

    return ""


def parse_rule(rule):
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
                left_seq, right_seq = cntx_seq[:idx], cntx_seq[idx + 1 :]
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
        post_seq = [BackRef(i) for i, _ in enumerate(left_seq)] + post_seq
        post_seq += [
            BackRef(i + offset_left + offset_ante) for i, _ in enumerate(right_seq)
        ]

    return ante_seq, post_seq


# TODO: __repr__, __str__, and __hash__ should deal with ante and post, not source
class Rule:
    def __init__(self, source):
        self.source = source
        self.ante, self.post = parse_rule(source)

    def __repr__(self):
        return repr(self.source)

    def __str__(self):
        return str(self.source)

    def __hash__(self):
        return hash(self.source)

    def __eq__(self, other):
        return self.source == other.source


def check_match(sequence, pattern):
    """
    Check if a sequence matches a given pattern.
    """

    # If there is a length mismatch, it does not match by definition. Note that
    # standard forward and backward operations will never pass sequences and patterns
    # mismatching in length, but it is worth to keep this check as the method can
    # be invoked directly by users, and the length checking is much faster than
    # performing the entire loop.
    if len(sequence) != len(pattern):
        return [False] * len(sequence)

    ret = True
    ret_list = []
    for token, ref in zip(sequence, pattern):
        ret = True
        if ref.type == "choice":
            # Check the sub-match for each alternative; if the alternative is a grapheme,
            # carry any modifier
            # TODO: have `in` iterator
            alt_matches = [all(check_match([token], [alt])) for alt in ref.choices]

            # TODO: address negation
            if not any(alt_matches):
                ret = False
        elif ref.type == "set":
            # Check if it is a set correspondence, which effectively works as a
            # choice here (but we need to keep track of) which set alternative
            # was matched
            alt_matches = [all(check_match([token], [alt])) for alt in ref.choices]

            # As in this case we need to know which alternative in set had a match,
            # instead of returning a boolean we will return the index of such
            # alternative. To make the logic more transparent, we shift the index
            # of one unit, so that no match will be returned as a zero.
            # Note that this code, following PEG principles, will always the return
            # the index of the first matched element, even if there are more than one.
            if not any(alt_matches):
                ret = False
            else:
                ret = alt_matches.index(True) + 1
        elif ref.type == "segment":
            # TODO: currently working only with monosonic segments
            # If the reference segment is not partial, we can just compare `token` to
            # `ref.segment`; if it is partial, we can compare the sounds in each
            # with the `>=` overloaded operator, which also involves making sure
            # `token` itself is a segment
            if not ref.segment.sounds[0].partial:
                ret = token == ref.segment
            else:
                if not isinstance(token, maniphono.Segment):
                    ret = False
                else:
                    ret = token.sounds[0] >= ref.segment.sounds[0]
        elif ref.type == "boundary":
            ret = token == "#"
        # TODO: sound classes, partial match

        # Append to the return list, so that we carry extra information like which
        # element of a set matched. Most of the time, this list will be composed
        # only of booleans.
        ret_list.append(ret)

    return ret_list


def _forward_translate(sequence, rule, match_list):
    post_seq = []

    # Build a list of indexes from `match_list`, which will be used in sequence in
    # case of sets
    indexes = [v for v in match_list if v is not True]

    # Iterate over all entries
    for entry in rule.post:
        # Note that this will, as intended, skip over `null`s
        # TODO: deal with sound classes
        if entry.type == "segment":
            post_seq.append(entry.segment)
        elif entry.type == "set":
            # The -1 in the `match` index is there to offset the +1 applied by
            # `check_match()`, so that we can differentiate False from zero.
            idx = indexes.pop(0) - 1
            post_seq.append(entry.choices[idx].segment)
        elif entry.type == "backref":
            # TODO: deal with "correspondence"
            # TODO: apply any modifier
            token = sequence[entry.index]
            post_seq.append(token)

    return post_seq


def forward(ante_seq, rule):
    """
    Apply forward transformation to a sequence given a rule.
    """

    # Build a sequence with boundaries, if that is the case (as in most cases),
    # as they are "dummy" graphemes
    if ante_seq.boundaries:
        iter_seq = ["#"] + ante_seq[:] + ["#"]
    else:
        iter_seq = ante_seq[:]

    # Iterate over the sequence, checking if subsequences match the specified `ante`.
    # We operate inside a `while True` loop because we don't allow overlapping
    # matches, and, as such, the `idx` might be updated either with +1 (looking for
    # the next position) or with the match length. While the whole logic could be
    # performed with a more Python list comprehension, for easier conversion to
    # other languages it is better to keep it as dumb loop.
    idx = 0
    post_seq = []
    while True:
        sub_seq = iter_seq[idx : idx + len(rule.ante)]
        match = check_match(sub_seq, rule.ante)
        if all(match):
            post_seq += _forward_translate(sub_seq, rule, match)
            idx += len(rule.ante)
        else:
            post_seq.append(iter_seq[idx])
            idx += 1

        if idx == len(iter_seq):
            break

    # TODO: post_seq should be a sequence, and we should take care of setting
    # .boudaries if necessary

    return post_seq


def main():
    # Read resources and try to parse them all
    with open("resources/sound_changes2.tsv") as tsvfile:
        for row in csv.DictReader(tsvfile, delimiter="\t"):
            print()
            print(row)
            ante = maniphono.parse_sequence(row["TEST_ANTE"])
            post = maniphono.parse_sequence(row["TEST_POST"])
            rule = Rule(row["RULE"])

            fw = forward(ante, rule)
            fw_str = " ".join([str(v) for v in fw])
            if fw_str[0] == "#":
                fw_str = fw_str[2:]
            if fw_str[-1] == "#":
                fw_str = fw_str[:-2]
            # fw = maniphono.Sequence(fw)
            print("FW", fw_str, fw_str == row["TEST_POST"].replace("g", "ɡ"))
            input()


if __name__ == "__main__":
    main()
