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

# Import Python libraries
import re

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
        """
        Returns the number of regex-representable elements.

        Note that this does *not* count empty segments, which means that
        .__len__() might, as intended, return a value lower than
        len(self.value)
        """

        return [isinstance(t, Empty) for t in self.value].count(False)

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
        # Whether to expand the sound-class short-hand, as in capture groups
        # for forward reconstruction, or not, as in backward reconstruction
        expand = kwargs.get("expand", True)

        if expand:
            ret = r"%s" % self.sound_classes[self.value]["regex"]
        else:
            ret = r"%s" % self.value

        return ret


class BackRef(Primitive):
    """
    Class for representing a back-referece.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, value, modifier=None):
        # pylint: disable=useless-super-delegation
        super().__init__(value)

        # Store the modifier, if it exists
        # TODO: for the time being, just dumbly rebuilding the modifier
        if not modifier:
            self.modifier = None
        else:
            features = []
            for feature in modifier['feature_desc']:
                if feature['value'] in "+-!":
                    feature_str = "%s%s" % (feature['value'], feature['key'])
                else:
                    feature_str = "%s=%s" % (feature['key'], feature['value'])
                features.append(feature_str)

            self.modifier = "[%s]" % ",".join(features)

    def __repr__(self):
        if not self.modifier:
            ret = "(@:%i)" % self.value
        else:
            ret = "(@:%i:%s)" % (self.value, str(self.modifier))

        return ret

    def to_regex(self, **kwargs):
        offset = kwargs.get("offset", 0)

        if not self.modifier:
            ret = r"\%i" % (self.value + offset)
        else:
            ret = r"\%i%s" % (self.value + offset, str(self.modifier))

        return ret


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
        alternatives = "|".join(
            [segment.to_regex(**kwargs) for segment in self.value]
        )
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
        capture = kwargs.pop("capture", None)

        # Collect the regex representation of all existing segments
        seq = [segment.to_regex(**kwargs) for segment in self.value]
        if capture:
            seq = [r"(%s)" % segment_rx for segment_rx in seq if segment_rx]

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
        return BackRef(int(ast["back_ref"]), ast["modifier"])

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


# NOTE: While the logic for ForwardAutomata and BackwardAutomata is
# similar enough to theoretically justify a single class returning both,
# skipping over repeated computations, for matters of code organization
# and considering future expansions it was decided to keep them as
# separate and independent classes (both inheriting from ReconsAutomata,
# of course).


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


class BackwardAutomata(ReconsAutomata):
    """
    Compiler for compiling ASTs into backward reconstruction replacements.
    """

    def compile_start(self, ast):
        # While too many locals are indeed a bad practice, this is one
        # of the cases where splitting the flow in different
        # methods/functions would decrease readibility
        # pylint: disable=too-many-locals

        # Collect compiled `source` and `target`, as well as
        # `left` and `right` contexts if available
        source = self.compile(ast["source"])
        target = self.compile(ast["target"])
        left, right = self.compile_context(ast)

        # Build the left and right sequences for source, composed entirely
        # of back references
        source_left = Sequence([BackRef(i + 1) for i, _ in enumerate(left)])
        source_right = Sequence([BackRef(i + 1) for i, _ in enumerate(right)])

        # Cache lens
        offset_left = len(left)
        offset_middle = len(left) + len(target)

        # Build the source and target sequences as list of tokens
        target_seq = " ".join(
            [
                left.to_regex(offset=0, capture=True),
                target.to_regex(offset=offset_left, capture=True),
                right.to_regex(offset=offset_middle, capture=True),
            ]
        ).split()

        source_seq = " ".join(
            [
                source_left.to_regex(offset=0),
                source.to_regex(offset=offset_left, expand=False),
                source_right.to_regex(offset=offset_middle),
            ]
        ).split()

        # We are almost ready to build the regexes, but the backward references
        # in the notation become forward ones in this case: for a rule
        # such as "C N -> @1 / _ #", at this point we would have `target`
        # as ' (\\1) (#) ' and `source` as ' :C: :N: \\2 ', needing to
        # swap the \\1 with :C:. We cannot do this above because we don't
        # know the offsets in advance, so that at this point it is just
        # easier to manipulate the strings before joining them. We iterate
        # over all regex items in `target_seq` and, if it is a back-reference,
        # we copy the corresponding `source_seq` value in place, making
        # note of the operation and correcting `source_seq` at the end
        # (we cannot plainly swap, as there might be multiple references to
        # same source item in target, so that the value must persist until
        # the end)
        corrected_target_seq = []
        source_corrections = {}
        for target_idx, segment in enumerate(target_seq):
            match = re.match(r"\(\\(\d+)\)", segment)
            if match:
                # -1 and +1 for dealing with lists which are 0-based
                # and regexes which are 1-based
                source_idx = int(match.group(1)) - 1
                source_corrections[source_idx] = target_idx + 1

                # We also need to add capturing parentheses
                corrected_target_seq.append(r"(%s)" % source_seq[source_idx])
            else:
                corrected_target_seq.append(segment)

        corrected_source_seq = [
            segment
            if source_idx not in source_corrections
            else r"\%i" % source_corrections[source_idx]
            for source_idx, segment in enumerate(source_seq)
        ]

        # build regexes
        target_rx = utils.clean_regex(" ".join(corrected_target_seq))
        source_rx = utils.clean_regex(" ".join(corrected_source_seq))

        return target_rx, source_rx
