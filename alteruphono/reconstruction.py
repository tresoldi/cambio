# encoding: "utf-8"

"""
Defines class for building reconstruction replacements from ASTs.

Internally, both forward and back reconstructions work by first
translating the ASTs into simple objects, all inheriting from
class `Primitive`, which offer a `.__repr__()` method, for debugging,
and a `.to_regex()` method for generating the regular expression
representation. `IterPrimitive` works as a list, allowing to
collect either Expressions or Sequences.
"""

# Import `alteruphono` modules
from . import compiler
from . import utils

# Define primitives for the automata: these are passed between the methods
# when building the multiple potential sequences, but also have an
# output method that allows to generate the correct (in this case, regex)
# expression when building the output itself. IterPrimitive is the
# one which works like a list (iterable).
class Primitive:
    """
    Class for representing an AST primitive.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, value=None):
        """
        Initializes a primitive for an AST element.
        """

        self.value = value

    def __repr__(self):
        """
        Returns a textual representation of the primitive, for debugging.
        """

        return NotImplemented

    def to_regex(self, **kwargs):
        """
        Return a raw string with the regex representation of the primitive.
        """
        # pylint: disable=no-self-use,unused-argument

        return NotImplemented


# TODO: move to system list-iterator, also checking if a list is passed
class IterPrimitive(Primitive):
    """
    Class for representing an iterable AST primitive.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        # pylint: disable=useless-super-delegation
        super().__init__(value)

        # Initialize the iter counter to -1
        self.i = -1

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        """
        Standard __iter__() method, returning itself.
        """

        return self

    def __next__(self):
        """
        Standard __next__ method.
        """
        if self.i == len(self.value) - 1:
            raise StopIteration

        self.i += 1
        return self.value[self.i]


class IPA(Primitive):
    """
    Class for representing an IPA grapheme.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        # pylint: disable=useless-super-delegation
        super().__init__(value)

    def __repr__(self):
        return "(I:%s)" % self.value

    def to_regex(self, **kwargs):
        return r"%s" % self.value


# TODO: implement modifier operations
class SoundClass(Primitive):
    """
    Class for representing a sound class.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, value, sound_classes):
        # pylint: disable=useless-super-delegation
        super().__init__(value)

        self.sound_classes = sound_classes

    def __repr__(self):
        return "(C:%s)" % self.value

    def to_regex(self, **kwargs):
        regex = self.sound_classes[self.value]["regex"]
        regex = ":%s:" % self.value
        return r"%s" % regex


class BackRef(Primitive):
    """
    Class for representing a back-referece.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        # pylint: disable=useless-super-delegation
        super().__init__(value)

    def __repr__(self):
        return "(@:%i)" % self.value

    def to_regex(self, **kwargs):
        offset = kwargs.get("offset", 0)
        return r"\%i" % (self.value + offset)


class Boundary(Primitive):
    """
    Class for representing a boundary.
    """

    # pylint: disable=too-few-public-methods

    def __init(self):
        # pylint: disable=useless-super-delegation
        super().__init__()

    def __repr__(self):
        return "(B:#)"

    def to_regex(self, **kwargs):
        return r"#"


class Empty(Primitive):
    """
    Class for representing an empty symbol (deletion).
    """

    # pylint: disable=too-few-public-methods

    def __init(self):
        # pylint: disable=useless-super-delegation
        super().__init__()

    def __repr__(self):
        return "(∅)"

    def to_regex(self, **kwargs):
        return r""


class Expression(IterPrimitive):
    """
    Class for representing an expression.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        # pylint: disable=useless-super-delegation
        super().__init__(value)

    def __repr__(self):
        return "{%s}" % ";".join([repr(v) for v in self.value])

    def to_regex(self, **kwargs):
        # TODO: check if we need to pass `kwargs`
        alternatives = "|".join([segment.to_regex() for segment in self.value])
        return r"%s" % alternatives


class Sequence(IterPrimitive):
    """
    Class for representing a sequence.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, value):
        # pylint: disable=useless-super-delegation
        super().__init__(value)

    def __repr__(self):
        return "-%s-" % "-".join([repr(v) for v in self.value])

    def to_regex(self, **kwargs):
        offset = kwargs.get("offset", None)
        capture = kwargs.get("capture", None)

        # Collect the regex representation of all segments
        seq = [segment.to_regex(offset=offset) for segment in self.value]
        if capture:
            seq = [r"(%s)" % segment_rx for segment_rx in seq]

        return r" ".join(seq)


class ReconsAutomata(compiler.Compiler):
    """
    Compiler for compiling ASTs into sets of reconstruction replacements.

    Serves as a super class for forward and backward reconstructions.
    """

    def __init__(self, sound_classes, debug=False):
        """
        Entry point for the `Graph` class.
        """

        # Call super()
        super().__init__(debug)

        # Store the sound class mapping, that will be given to every
        # SoundClass primitive we might run into.
        self.sound_classes = sound_classes

    def compile_ipa(self, ast):
        return IPA(ast["ipa"]["ipa"])

    def compile_sound_class(self, ast):
        # TODO: pass and handle modifiers
        return SoundClass(ast["sound_class"]["sound_class"], self.sound_classes)

    def compile_boundary(self, ast):
        return Boundary()

    def compile_empty(self, ast):
        return Empty()

    def compile_position(self, ast):
        return "_pos_"

    def compile_back_ref(self, ast):
        # TODO: pass and handle modifiers
        return BackRef(int(ast["back_ref"]))

    def compile_feature_desc(self, ast):
        return "(%s)" % ast["feature_desc"]

    def compile_sequence(self, ast):
        return Sequence([self.compile(segment) for segment in ast["sequence"]])

    def compile_expression(self, ast):
        # Alternatives always hold sequences (even if it is a single grapheme,
        # for example, it is a sequence of a single grapheme), and we
        # collect them as lists (i.e., Expressions) in all cases.
        return Expression([self.compile(alt) for alt in ast["expression"]])

    def compile_context(self, ast):
        # By default, no left nor right context
        left, right = Sequence([]), Sequence([])

        if ast.get("context"):
            # We first look for the index of the positional "_" segment in
            # context, so that we can separate preceding and following parts;
            # we build "fake" AST trees as Python dictionaries, making it
            # simpler and using the same .get() method
            seq = ast["context"]["sequence"]
            idx = [
                segment.get("position") is not None for segment in seq
            ].index(True)

            # Collect all segments left and right
            left = Sequence([self.compile(seg) for seg in seq[:idx]])
            right = Sequence([self.compile(seg) for seg in seq[idx + 1 :]])

        return left, right

    def compile_start(self, ast):
        return NotImplemented


class ForwardAutomata(ReconsAutomata):
    """
    Compiler for compiling ASTs into forward reconstruction replacements.
    """

    def compile_start(self, ast):
        # Collect compiled `source` and `target`, as well as
        # `left` and `right` contexts if available
        source = self.compile(ast["source"])
        target = self.compile(ast["target"])
        left, right = self.compile_context(ast)

        # Build the left and right sequences for target, composed entirely
        # of back references
        target_left = Sequence([BackRef(i + 1) for i, _ in enumerate(left)])
        target_right = Sequence([BackRef(i + 1) for i, _ in enumerate(right)])

        # Cache lens
        offset_left = len(left)
        offset_middle = len(left) + len(source)

        # Build the source and target regexes
        source_rx = " ".join(
            [
                left.to_regex(offset=0, capture=True),
                source.to_regex(offset=offset_left, capture=True),
                right.to_regex(offset=offset_middle, capture=True),
            ]
        )

        target_rx = " ".join(
            [
                target_left.to_regex(offset=0),
                target.to_regex(offset=offset_left),
                target_right.to_regex(offset=offset_middle),
            ]
        )

        source_rx = utils.clean_regex(source_rx)
        target_rx = utils.clean_regex(target_rx)

        return source_rx, target_rx
