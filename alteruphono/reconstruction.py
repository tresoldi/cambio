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

    def output(self):
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
        if self.i == len(self.value)-1:
            raise StopIteration

        self.i += 1
        return self.value[self.i]

class IPA(Primitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "(I:%s)" % self.value

    def output(self):
        return "/%s/" % self.value


class SoundClass(Primitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "(C:%s)" % self.value

    def output(self):
        return "%s" % self.value


class BackRef(Primitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "(@:%i)" % self.value

    def output(self):
        return "@%i" % self.value


class Boundary(Primitive):
    def __init(self):
        super().__init__()

    def __repr__(self):
        return "(B:#)"

    def output(self):
        return None


class Empty(Primitive):
    def __init(self):
        super().__init__()

    def __repr__(self):
        return "(∅)"

    def output(self):
        return None


class Expression(IterPrimitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "{%s}" % ";".join([repr(v) for v in self.value])

    def output(self):
        # TODO: depends if source/target and output?
        return NotImplemented

class Sequence(IterPrimitive):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return "-%s-" % "-".join([repr(v) for v in self.value])

    def output(self):
        # TODO: depends if source/target and output?
        return NotImplemented


class ReconsAutomata(compiler.Compiler):
    """
    Compiler for compiling ASTs into sets of reconstruction replacements.
    """

    def __init__(self, debug=False):
        """
        Entry point for the `Graph` class.
        """

        # Call super()
        super().__init__(debug)

    def compile_ipa(self, ast):
        return IPA(ast["ipa"]["ipa"])

    def compile_sound_class(self, ast):
        # TODO: pass and handle modifier
        return SoundClass(ast["sound_class"]["sound_class"])

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
            # Return empty iterator
            left = Sequence([])
            right = Sequence([])
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

        return left, right

    def compile_start(self, ast):
        # Collect `source` and `target` blocks
        source = self.compile(ast["source"])
        target = self.compile(ast["target"])
        print("S:", source)
        print("T:", target)

        # Collect "context" if available (also a sequence), split in
        # `preceding` (to the left) and `following` (to the right) parts.
        # These are used for source context, as the target context will
        # be composed entirely of back-references due to alternatives
        # (e.g., with a rule `a -> e / _ i/u` allows mappings like
        # `a i -> e i` but *not* `a i -> e u`).
        left, right = self.compile_context(ast)
        print("L:", left)
        print("R:", right)
        left_pat = list(itertools.product(*left))
        right_pat = list(itertools.product(*right))
#        left = [opt for opt in list(itertools.product(*left)) if opt]
#        right = [opt for opt in list(itertools.product(*right)) if opt]
        print("Lp:", left_pat)
        print("Rp:", right_pat)
        return

        # Build the regular expression patterns; in the initial product,
        # we need a list comprehension to clean the pattern, as
        # `itertools.product()` will return an empty list if any of the
        # elements is an empty list itself.
        #        source_pat = [part for part in [left, source, right] if part]
        #        print("-", len(source_pat), source_pat)
        #        source_prod = list(itertools.product(source_pat))
        #        print("sprod:", len(source_prod), source_prod)

        source_prod = list(itertools.product([left], [source], [right]))
        print("sprod:", len(source_prod), source_prod)

        # Map all patterns to regular expression strings
        source_regexes = [
            " ".join([str(v[0]) for v in pat if v]) for pat in source_prod
        ]
        for i, (pat, reg) in enumerate(zip(source_prod, source_regexes)):
            print("Sp #%i: %s -> [%s]" % (i, pat, reg))

        # Build source and target patterns, removing empty items
        # TODO: replace the `:null:` check if/when moving to objects
        #        source_pat = [e for e in left + source + right if e and e != ":null:"]
        #        target_pat = [e for e in left + target + right if e and e != ":null:"]

        return left + source + right
