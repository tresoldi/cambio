# encoding: "utf-8"

"""
Defines class for building reconstruction replacements from ASTs.
"""

# Import `alteruphono` modules
from . import compiler

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
        return "(ipa:%s)" % ast["ipa"]["ipa"]

    def compile_sound_class(self, ast):
        return "(SC:%s)" % ast["sound_class"]["sound_class"]

    def compile_boundary(self, ast):
        return "#"

    def compile_empty(self, ast):
        return ":null:"

    def compile_position(self, ast):
        return "_pos_"

    def compile_back_ref(self, ast):
        return "@%s" % ast["back_ref"]

    def compile_feature_desc(self, ast):
        return "(%s)" % ast["feature_desc"]

    def compile_sequence(self, ast):
        return [self.compile(segment) for segment in ast["sequence"]]

    def compile_alternative(self, ast):
        # Alternatives always hold sequences (even if it is a single grapheme,
        # for example, it is a sequence of a single grapheme). As such, we
        # collect the textual description of each alternative as a sequence,
        # before joining the text and returning.
        # NOTE: working around what seems to be a problem in TatSu
        if len(ast["alternative"]) == 1:
            ret = self.compile(ast["alternative"][0])
        else:
            descriptors = [
                self.compile(altern) for altern in ast["alternative"]
            ]

            ret = descriptors

        return ret

    def compile_context(self, ast):
        preceding_text, following_text = None, None

        if ast.get("context"):
            # We first look for the index of the positional "_" segment in
            # context, so that we can separate preceding and following parts;
            # we build "fake" AST trees as Python dictionaries, making it
            # simpler and using the same .get() method
            idx = [
                segment.get("position") is not None
                for segment in ast["context"]["sequence"]
            ].index(True)

            preceding = {"sequence": ast["context"]["sequence"][:idx]}
            following = {"sequence": ast["context"]["sequence"][idx + 1 :]}

            # We could call the `.compile_sequence` directly, but it is
            # better to keep the logic of a single place handling everything.
            if preceding["sequence"]:
                preceding_text = self.compile(preceding)
            if following["sequence"]:
                following_text = self.compile(following)

            print("P",  preceding_text)
            print("F", following_text)

        # default to empty lists, when non existing
        preceding_text = preceding_text or []
        following_text = following_text or []

        return preceding_text, following_text

    def compile_start(self, ast):
        # Collect `source` and `target` blocks
        source = self.compile(ast["source"])
        target = self.compile(ast["target"])

        # TODO: context decomposition should be permanent within an option:
        # `a -> e / _ i|u` allows mappings like `a i -> e i` but *not*
        # `a i -> e u` -- in a way, it is a backrefence in the target
        # context (they are entangled)

        # Collect "context" if available (also a sequence)
        preceding, following = self.compile_context(ast)

        # Build source and target patterns, removing empty items
        # TODO: replace the `:null:` check if/when moving to objects
        source_pat = [e for e in preceding + source + following if e and e != ":null:"]
        target_pat = [e for e in preceding + target + following if e and e != ":null:"]

        print("S:", source_pat)
        print("T:", target_pat)

        return preceding + source + following
