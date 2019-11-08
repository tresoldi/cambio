# encoding: "utf-8"

"""
Defines class for building reconstruction replacements from ASTs.
"""
# Import Python standard libraries
import itertools

# Import `alteruphono` modules
from . import compiler

# Define primitives for the automata: these are passed between the methods
# when building the multiple potential sequences, but also have an
# output method that allows to generate the correct (in this case, regex)
# expression when building the output itself. IterPrimitive is the
# one which works like a list (iterable).
class Primitive:
    def __init__(self, value=None):
        self.value = value

    def to_regex(self):
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

    def to_regex(self):
        return self.value


class SoundClass(Primitive):
    def __init__(self, value, sound_classes):
        super().__init__(value)

        self.sound_classes = sound_classes

    def __repr__(self):
        return "(C:%s)" % self.value

    def to_regex(self):
        # TODO: modifier operations
        return self.sound_classes[self.value]["description"]


class BackRef(Primitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "(@:%i)" % self.value

    def to_regex(self):
        return "\\%i" % self.value


class Boundary(Primitive):
    def __init(self):
        super().__init__()

    def __repr__(self):
        return "(B:#)"

    def to_regex(self):
        return "#"


class Empty(Primitive):
    def __init(self):
        super().__init__()

    def __repr__(self):
        return "(∅)"

    def to_regex(self):
        return ""


class Expression(IterPrimitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "{%s}" % ";".join([repr(v) for v in self.value])

    def to_regex(self):
        return "|".join([segment.to_regex() for segment in self.value])


class Sequence(IterPrimitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "-%s-" % "-".join([repr(v) for v in self.value])

    def to_regex(self):
        return " ".join([segment.to_regex() for segment in self.value])


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
        # Collect `source` and `target` blocks
        source = self.compile(ast["source"])
        target = self.compile(ast["target"])
        print("S:", len(source), source)
        print("T:", len(target), target)

        # Collect "context" if available (also a sequence), split in
        # preceding (to the `left`) and following (to the `right`) parts.
        # These are used for source context, as the target context will
        # be composed entirely of back-references due to alternatives
        # (e.g., with a rule `a -> e / _ i/u` allows mappings like
        # `a i -> e i` but *not* `a i -> e u`). From there, we can obtain
        # a list of left and right patterns that will be combined with
        # source and target later.
        left, right = self.compile_context(ast)
        left_pat = list(itertools.product(*left))
        right_pat = list(itertools.product(*right))
        print("Lpat:", len(left_pat), left_pat)
        print("Rpat:", len(right_pat), right_pat)

        # Build the source and target pattern. As regexes will take care
        # of alternatives in the parts that are actually replaced, here
        # we don't need to decompose alternative expressions as in the
        # case of context.
        # As the source and target might be entangled -- e.g., if the
        # source context is # `# S _`, the only way to know which sound of
        # class S (which can also carry modifiers) was matched is to
        # capture an reference it. As the source and target themselves
        # can use back-references, we need to first use two different
        # series of back-references (one for source/target and another
        # for context), mapping to a single one once the strings are
        # ready.
        source_pat = [
            list(
                itertools.chain.from_iterable(
                    [segment for segment in pat if segment]
                )
            )
            for pat in itertools.product(left_pat, [source], right_pat)
        ]
        target_pat = [
            list(
                itertools.chain.from_iterable(
                    [segment for segment in pat if segment]
                )
            )
            for pat in itertools.product(left_pat, [target], right_pat)
        ]

        # Map all patterns to regular expressions, skipping over empty
        # values (such as ":null:")
        source_rx = [
            [segment.to_regex() for segment in pattern if segment.to_regex()]
            for pattern in source_pat
        ]
        target_rx = [
            [segment.to_regex() for segment in pattern if segment.to_regex()]
            for pattern in target_pat
        ]

        for idx, (p, t, p_rx, t_rx) in enumerate(
            zip(source_pat, target_pat, source_rx, target_rx)
        ):
            print("#%i [%s] -> [%s]" % (idx, p, t))
            print([type(v) for v in p])
            print(p_rx, t_rx)

        return
