# new, ongoing parser with regular expressions

import csv
import re
import unicodedata
import itertools

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


def preprocess(rule):
    """
    Internal function for pre-processing of rules.
    """

    # 1. Normalize to NFD, as per maniphono
    rule = unicodedata.normalize("NFD", rule)

    # 2. Replace multiple spaces with single ones, and remove leading/trailing spaces
    rule = re.sub(r"\s+", " ", rule.strip())

    return rule


# TODO: is this still used?
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
        mod = match.group("mod")
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


def parse_seq_as_rule(seq):
    seq = preprocess(seq)
    return [parse_atom(atom) for atom in seq.strip().split()]


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
                if not isinstance(token, maniphono.SoundSegment):
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
            if entry.modifier:
                # TODO: drop-in solution for the +
                mod = entry.modifier.replace("+", "")
                token.sounds[0] += mod

            post_seq.append(token)

    return post_seq


def forward(ante_seq, rule):
    """
    Apply forward transformation to a sequence given a rule.
    """

    # Build a sequence with boundaries, if that is the case (as in most cases),
    # as they are "dummy" graphemes
    #    if ante_seq.boundaries:
    #        iter_seq = ["#"] + ante_seq[:] + ["#"]
    #    else:
    #        iter_seq = ante_seq[:]

    iter_seq = ante_seq.as_list()

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


def _backward_translate(sequence, rule, match_list):
    # Collects all information we have on what was matched, in terms of back-references
    # and classes/features, from what we have in the reflex
    value = {}
    no_nulls = [token for token in rule.post if token.type != "null"]
    for post_entry, token in zip(no_nulls, sequence):
        if post_entry.type == "backref":
            # TODO: apply modifier inverse
            value[post_entry.index] = token

    # NOTE: `ante_seq` is here the modified one for reconstruction, not the one in the rule
    ante_seq = []
    for idx, (ante_entry, match) in enumerate(zip(rule.ante, match_list)):
        if ante_entry.type == "choice":
            ante_seq.append(value.get(idx, "C|V"))
        elif ante_entry.type == "set":
            ante_seq.append(value.get(idx, "C|V"))
        elif ante_entry.type == "segment":
            ante_seq.append(ante_entry.segment)

    # Depending on the type of rule that was applied, the `ante_seq` list
    # might at this point have elements expressing more than one
    # sound and expressing alternatives that need to be computed
    # with a product (e.g., `['#'], ['d'], ['i w', 'j u'], ['d'] ['#']`).
    # This correction is performed by the calling function, also allowing
    # to return a `Sequence` instead of a plain string (so that we also
    # deal with missing boundaries, etc.). We also return the unaltered,
    # original `sequence`, expressing cases where no changes were
    # applied.
    return [
        sequence,
        ante_seq,
    ]


# TODO: make sure it works with repeated backreferences, such as "V s > @1 z @1",
# which we *cannot* have mapped only as "V z V"
def backward(post_seq, rule):
    post_seq = post_seq.as_list()

    # This method makes a copy of the original AST ante-tokens and applies
    # the modifiers from the post sequence; in a way, it "fakes" the
    # rule being applied, so that something like "d > @1[+voiceless]"
    # is transformed in the equivalent "t > @1".
    # TODO: add modifiers, as per previous implementarion
    def _add_modifier(ante_token, post_token):
        return ante_token

    # Compute the `post_ast`, applying modifiers and skipping nulls
    post_ast = [token for token in rule.post if token.type != "null"]
    post_ast = [
        token
        if token.type != "backref"
        else _add_modifier(rule.ante[token.index], token)
        for token in post_ast
    ]

    # Iterate over the sequence, checking if subsequences match the specified `post`.
    # We operate inside a `while True` loop because we don't allow overlapping
    # matches, and, as such, the `idx` might be updated either with +1 (looking for
    # the next position) or with the match length. While the whole logic could be
    # performed with a more Python list comprehension, for easier conversion to
    # other languages it is better to keep it as dumb loop.
    # TODO: note same comment as `forward`, maybe join methods?
    idx = 0
    ante_seqs = []
    while True:
        # TODO: address comment from original implementation
        sub_seq = post_seq[idx : idx + len(post_ast)]
        match = check_match(sub_seq, post_ast)

        if len(match) == 0:
            break
        if all(match):
            ante_seqs.append(_backward_translate(sub_seq, rule, match))
            idx += len(post_ast)
        else:
            ante_seqs.append(maniphono.Sequence([post_seq[idx]], boundaries=False))
            idx += 1

        if idx == len(post_seq):
            break

    # Computes the product of possibilities
    # TODO: organize and do it properly
    ante_seqs = [candidate for candidate in itertools.product(*ante_seqs)]

    ret = []
    for i, a in enumerate(ante_seqs):
        chain = list(itertools.chain.from_iterable(a))
        chain = [t for t in chain if t != "#"]
        ret.append(chain)

    return ret


def main():
    # Read resources and try to parse them all
    with open("resources/sound_changes2.tsv") as tsvfile:
        for row in csv.DictReader(tsvfile, delimiter="\t"):
            # skip negations
            if "!" in row["RULE"]:
                continue

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

            fw_match = fw_str == row["TEST_POST"].replace("g", "ɡ")

            bw = backward(post, rule)
            bw_strs = [" ".join([str(v) for v in bw_str]) for bw_str in bw]

            # TODO: deal with [ and ] currently stripped with [1:-1]
            bw_rules = [
                parse_seq_as_rule(str(maniphono.Sequence(cand))[1:-1]) for cand in bw
            ]
            bw_match = any(
                [all(check_match(ante.as_list(), bw_rule)) for bw_rule in bw_rules]
            )

            print("FW", fw_match, "|", fw_str, "|")
            print("BW", bw_match, "|", bw_strs, "|")

            if not all([fw_match, bw_match]):
                input()


if __name__ == "__main__":
    main()
