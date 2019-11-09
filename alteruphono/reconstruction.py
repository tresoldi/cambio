# encoding: "utf-8"

"""
Defines class for building reconstruction replacements from ASTs.
"""
# Import Python standard libraries
import itertools
from string import ascii_lowercase

# Import `alteruphono` modules
from . import compiler

# TODO: move to utils
# define a label iterator
# -> "a", "b", ..., "aa", "ab", ..., "zz", "aaa", "aab", ...
# def label_iter():
#    for length in itertools.count(1):
#        for chars in itertools.product(ascii_lowercase, repeat=length):
#          yield "".join(chars)


# Define primitives for the automata: these are passed between the methods
# when building the multiple potential sequences, but also have an
# output method that allows to generate the correct (in this case, regex)
# expression when building the output itself. IterPrimitive is the
# one which works like a list (iterable).
class Primitive:
    def __init__(self, value=None):
        self.value = value

    def to_regex(self, **kwargs):
        # NOTE: should include the capture if needed, etc.
        return NotImplemented


class IterPrimitive(Primitive):
    def __init__(self, value):
        self.value = value

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        self.i = -1
        return self

    def __next__(self):
        if self.i == len(self.value) - 1:
            raise StopIteration

        self.i += 1
        return self.value[self.i]


class IPA(Primitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "(I:%s)" % self.value

    def to_regex(self, **kwargs):
        return r"%s" % self.value


class SoundClass(Primitive):
    def __init__(self, value, sound_classes):
        super().__init__(value)

        self.sound_classes = sound_classes

    def __repr__(self):
        return "(C:%s)" % self.value

    def to_regex(self, **kwargs):
        # TODO: modifier operations
        v = self.sound_classes[self.value]["description"]
        v = ":%s:" % self.value
        return r"%s" % v


class BackRef(Primitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "(@:%i)" % self.value

    def to_regex(self, **kwargs):
        offset = kwargs.get("offset", 0)
        return r"\%i" % (self.value + offset)


class Boundary(Primitive):
    def __init(self):
        super().__init__()

    def __repr__(self):
        return "(B:#)"

    def to_regex(self, **kwargs):
        return r"#"


class Empty(Primitive):
    def __init(self):
        super().__init__()

    def __repr__(self):
        return "(∅)"

    def to_regex(self, **kwargs):
        return r""


class Expression(IterPrimitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "{%s}" % ";".join([repr(v) for v in self.value])

    def to_regex(self, **kwargs):
        # TODO: what to do if captures inside captures here
        v = "|".join([segment.to_regex() for segment in self.value])
        return "%s" % v


class Sequence(IterPrimitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "-%s-" % "-".join([repr(v) for v in self.value])

    def to_regex(self, capture, **kwargs):
        # TODO: comment about offset
        offset = kwargs.get("offset", None)

        # TODO: no capture here, right? passed from segment
        # TODO: note that we group-capture even boundaries
        # TODO: should default to `capture=None`?

        # Have a capture group around everything, even backreferences
        # NOTE: `if segment` allows to skip over empty symbols
        v = [
            segment.to_regex(offset=offset) for segment in self.value if segment
        ]
        if capture:
            v = [r"(%s)" % seg_r for seg_r in v]

        return r" ".join(v)


class ReconsAutomata(compiler.Compiler):
    """
    Compiler for compiling ASTs into sets of reconstruction replacements.
    """

    def __init__(self, sound_classes, debug=False):
        """
        Entry point for the `Graph` class.
        """

        # Call super()
        super().__init__(debug)

        self.sound_classes = sound_classes

    def compile_ipa(self, ast):
        return IPA(ast["ipa"]["ipa"])

    def compile_sound_class(self, ast):
        # TODO: pass and handle modifier
        return SoundClass(ast["sound_class"]["sound_class"], self.sound_classes)

    def compile_boundary(self, ast):
        return Boundary()

    def compile_empty(self, ast):
        return Empty()

    def compile_position(self, ast):
        return "_pos_"

    def compile_back_ref(self, ast):
        # TODO: pass and handle modifier
        return BackRef(int(ast["back_ref"]))

    def compile_feature_desc(self, ast):
        return "(%s)" % ast["feature_desc"]

    def compile_sequence(self, ast):
        return Sequence([self.compile(segment) for segment in ast["sequence"]])

    def compile_expression(self, ast):
        # Alternatives always hold sequences (even if it is a single grapheme,
        # for example, it is a sequence of a single grapheme). As such, we
        # collect the textual description of each alternative as a sequence,
        # before joining the text and returning.
        if len(ast["expression"]) == 1:
            ret = self.compile(ast["expression"][0])
        else:
            ret = Expression([self.compile(alt) for alt in ast["expression"]])

        return ret

    def compile_context(self, ast):
        if not ast.get("context"):
            left = []
            right = []
        else:
            # We first look for the index of the positional "_" segment in
            # context, so that we can separate preceding and following parts;
            # we build "fake" AST trees as Python dictionaries, making it
            # simpler and using the same .get() method
            seq = ast["context"]["sequence"]
            idx = [
                segment.get("position") is not None for segment in seq
            ].index(True)

            # For context, we want an Expression even when dealing with
            # single item lists, as, contrary to sequences in source and
            # target, this needs to be decomposed "by hand" before
            # generating the regular expressions or list of string
            # replacements (see comment and example in `.compile_start()`)
            left = Sequence([self.compile(alt) for alt in seq[:idx]])
            right = Sequence([self.compile(alt) for alt in seq[idx + 1 :]])

        # Make every segment in the sequence a single-item list, unless
        # it is an expression. This will allow to decompose the left and
        # right context with `itertools.product()` within the
        # `.compile_start()` method
        left = [
            [segment] if not isinstance(segment, Expression) else segment
            for segment in left
        ]
        right = [
            [segment] if not isinstance(segment, Expression) else segment
            for segment in right
        ]

        return left, right

    def compile_start(self, ast):
        # Define the `cap`ture `label` iterator that will be used for
        # this `start` symbol. Due to context entanglement and back-referneces,
        # as described in the comments below, all capture groups of the
        # regex must be named (luckily, Python captures groups both under the
        # name and the index).
        # Using a single infinite iterator as this guarantees
        # that no duplicates will be used (even though the capture labels
        # won't always start with a,b,c, which might make debugging a
        # a little more complex).
        # capture_iter = label_iter()

        # Collect "context" if available, split in
        # preceding (to the `left`) and following (to the `right`) parts.
        # In normal, forward reconstruction, these will be used for
        # the source context, as the target one will consist entirely of
        # back-references due to the need to carry alterantives
        # be composed entirely of back-references due to alternatives
        # (e.g., with a rule `a -> e / _ i/u` allows mappings like
        # `a i -> e i` but *not* `a i -> e u`). From there, we can obtain
        # a list of left and right patterns that will be combined with
        # source and target later.
        # TODO: note that we don't allow back-references in the context --
        #       if those are really needed (for cases like
        #       "C > \1[+voice] / V C \1"), they will need to be specified
        #       as source/target (in this case,
        #       "V C \1 > \1 \2[+voice] \1")
        left, right = self.compile_context(ast)
        left_pat = list(itertools.product(*left))
        right_pat = list(itertools.product(*right))
        print("L:", left, type(left))
        print("R:", right, type(right))
        print("Lpat:", len(left_pat), left_pat, type(left_pat))
        print("Rpat:", len(right_pat), right_pat, type(right_pat))

        # As the source and target might be entangled -- e.g., if the
        # source context is # `# S _`, the only way to know which sound of
        # class S (which can also carry modifiers) was matched is to
        # capture an reference it. As the source and target themselves
        # can use back-references, we need to first use two different
        # series of back-references (one for source/target and another
        # for context), mapping to a single one once the strings are
        # ready.
        left_patterns = [
            Sequence([segment for segment in pat if segment])
            for pat in left_pat
            if pat
        ]
        right_patterns = [
            Sequence([segment for segment in pat if segment])
            for pat in right_pat
            if pat
        ]

        print(
            "Lpts:",
            len(left_patterns),
            left_patterns,
            [len(p) for p in left_patterns],
        )
        print(
            "Rpts:",
            len(right_patterns),
            right_patterns,
            [len(p) for p in right_patterns],
        )

        # get source and target
        source = self.compile(ast["source"])
        target = self.compile(ast["target"])

        # collect [source_offset, target_offset, left+source, left+target]
        # pairs first, fixing
        # the backrefences in `source` and `target` by the offSets of
        # `left`
        # TODO: target segments should all be captures (sound classes, etc.),
        # as ----> #53 ['a -> æ / _ C e']
        # 0 S: [(a) (:C:) (e)]
        # 0 T: [æ :C: e]
        temp = []
        if not left_patterns:
            source_rx = source.to_regex(offset=0, capture=True)
            target_rx = target.to_regex(offset=0, capture=False)
            temp.append(
                [len(source) - 1, len(target) - 1, source_rx, target_rx]
            )
        else:
            for pattern in left_patterns:
                left_rx = pattern.to_regex(capture=True)
                source_rx = source.to_regex(offset=len(pattern), capture=True)
                target_rx = target.to_regex(offset=len(pattern), capture=False)
                temp.append(
                    [
                        len(pattern) + len(source),
                        len(pattern) + len(target),
                        "%s %s" % (left_rx, source_rx),
                        "%s %s" % (left_rx, target_rx),
                    ]
                )

        # add the right parts, with the offsets, collecting
        # all regex source/target pairs
        # TODO: there should be no back-reference in right_pat, right?
        pairs = []
        for option in temp:
            if not right_patterns:
                pairs.append([option[2], option[3]])
            else:
                for pattern in right_patterns:
                    source_right_rx = pattern.to_regex(
                        offset=option[0] - 1, capture=True
                    )
                    target_right_rx = pattern.to_regex(
                        offset=option[1] - 1, capture=False
                    )

                    # TODO: should strip here
                    pairs.append(
                        [
                            "%s %s" % (option[2], source_right_rx),
                            "%s %s" % (option[3], target_right_rx),
                        ]
                    )

        for idx, pair in enumerate(pairs):
            print("#%i S: [%s]" % (idx, pair[0]))
            print("#%i T: [%s]" % (idx, pair[1]))
