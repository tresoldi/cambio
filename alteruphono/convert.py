# encoding: utf-8

"""
Defines class for representing an AST with natural language.
"""

# Import Python libraries
from collections import defaultdict
import csv
import pprint
import re

# Import `alteruphono` modules
from . import compiler
from . import utils

# TODO: npte on no graphviz dependency
# TODO: accept a string with a description (could be the other transducer)
class Graph(compiler.Compiler):
    """
    Compiler for generating a .dot representation of an AST.

    Unlike the natural language compiler, this is not supposed to be used
    with any subset of an AST, but only with a full rule (i.e., including
    `source` and `target` symbols). For this, `compile_start()` will
    collect lists of nodes and edges that are combined into a single
    string before returning.
    """

    def __init__(self, debug=False):
        """
        Entry point for the `Graph` class.
        """

        # Call super()
        super().__init__(debug)

        # Internalize/clear internal variables
        self._clear_status()

    def _clear_status(self):
        self.nodes = {}
        self.edges = []

    # "Local" method

    def build_dot(self):
        """
        Returns the DOT representation of the graph internally determined.
        """

        # List all nodes
        nodes_str = [
            '\t%s [label="%s"] ;' % (key, value)
            for key, value in self.nodes.items()]

        # List all edges
        # NOTE: takes care of ports, if any
        edges_str = []
        for edge in self.edges:
            node_source = edge[0].split(":")
            node_target = edge[1].split(":")
            if len(node_source) == 1:
                node_source = '"%s"' % node_source[0]
            else:
                node_source = '"%s":%s' % (node_source[0], node_source[1])

            if len(node_target) == 1:
                node_target = '"%s"' % node_target[0]
            else:
                node_target = '"%s":%s' % (node_target[0], node_target[1])

            edges_str.append("\t%s -> %s ;" % (node_source, node_target))


        # List ranks (make sure everything is in the same line,
        # especially when back-reference edges are involved)
        rank_str = "{rank=same;%s} ;" % ";".join([node for node
        in self.nodes if node[0] in "STC"])

        # Build final string
        buf = """
        digraph G {
            graph [layout="dot",ordering="out",splines="polyline"] ;
            %s
            %s
            %s
        }""" % ("\n".join(nodes_str),
        "\n".join(edges_str), rank_str)

        return buf

    # Overriden methods

    def compile_ipa(self, ast):
        return "(ipa:%s)" % ast["ipa"]["ipa"]

    # TODO: take list of definitions as well, at least en?
    def compile_sound_class(self, ast):
        return "[SC:%s]" % ast["sound_class"]["sound_class"]

    def compile_boundary(self, ast):
        return "#"

    def compile_empty(self, ast):
        return ":null:"

    def compile_position(self, ast):
        return "_pos_"

    def compile_back_ref(self, ast):
        return "@%s" % ast["back_ref"]

    def compile_feature_desc(self, ast):
        return "[%s]" % ast["feature_desc"]

    def compile_sequence(self, ast):
        return [self.compile(segment) for segment in ast["sequence"]]

    # TODO: should add its own nodes
    def compile_alternative(self, ast):
        if len(ast["alternative"]) == 1:
            ret_text = self.compile(ast["alternative"][0])
        else:
            descriptors = [
                self.compile(altern) for altern in ast["alternative"]
            ]
            ret_text = "[alt:%s]" % "/".join(descriptors)

        return ret_text

    def compile_contex(self, ast):
        if ast.get("context"):
            return self.compile(ast["context"])

        return None

    def compile_start(self, ast):
        # Clear interval variables, allowing reuse
        self._clear_status()

        # Add nodes for source and target, as well as context if found
        self.nodes["source"] = "source"
        self.nodes["target"] = "target"
        self.edges.append(["start", "source"])
        self.edges.append(["start", "target"])

        # Add `source` nodes and edges
        for idx, segment in enumerate(self.compile(ast["source"])):
            self.nodes["S%i"%idx] = segment
            self.edges.append(["source", "S%i"%idx])

        # Add `target` nodes and edges
        for idx, segment in enumerate(self.compile(ast["target"])):
            self.nodes["T%i"%idx] = segment
            self.edges.append(["target", "T%i"%idx])

        # Add `context` nodes and edges, if any
        context = self.compile_contex(ast)
        if context:
            self.edges.append(["start", "context"])
            for idx, segment in enumerate(context):
                self.nodes["C%i"%idx] = segment
                self.edges.append(["context", "C%i"%idx])

        # Add edges for back-references
        # TODO: proper back-reference notation
        for node_name, node_text in self.nodes.items():
            if node_text[0] == "@":
                idx = int(node_text[1:])-1
                self.edges.append(['S%i:s'%idx,"%s:s"%node_name])

        ret = {"s":self.nodes,"e":self.edges}
#        pprint.pprint(ret)
        return str(ret)

# TODO: move to utils
def clean(text):
    """
    Cleans text, basically removing superflous spaces.
    """

    return re.sub(r"\s+", " ", text).strip()


class Translate(compiler.Compiler):
    """
    Compiler for representing an AST with natural language.

    The class includes an essential implementation of `gettext`, loading
    translations and replacements from the `resources/` dir, allowing
    for easier expansion.
    """

    def __init__(self, sound_classes, debug=False, **kwargs):
        """
        Entry point for the `Translate` class.
        """

        # Call super()
        super().__init__(debug)

        # Load and set properties, defaulting language to English
        self.sound_classes = sound_classes
        self.lang = kwargs.get("lang", "en")

        # Load translation data
        transfile = utils.RESOURCE_DIR / "translations.tsv"
        replfile = utils.RESOURCE_DIR / "translation_replacements.tsv"

        self._gettext = {}
        with open(transfile.as_posix()) as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                ref = row.pop("ref")
                self._gettext[ref] = row

        self._replacements = defaultdict(list)
        with open(replfile.as_posix()) as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                self._replacements[row["language"]].append(
                    [row["source"], row["target"]]
                )

    def _t(self, text, *args):
        """
        Custom and essential implementation of a `gettext` clone.
        """

        # Get translation and make argument replacement in the correct order
        translation = self._gettext[text].get(self.lang, text)
        for idx, arg in enumerate(args):
            translation = translation.replace("{%i}" % (idx + 1), arg)

        return translation

    # "Local" methods

    def _compile_modifier(self, ast):
        """
        Compile a modifier; note that this is not part of `Compiler`.
        """

        return self.compile(ast["modifier"])

    def _recons_label(self, ast):
        """
        Compile a "reconstrution" label, if any.
        """

        if ast.get("recons"):
            return self._t("reconstructed")

        return ""

    # Overriden methods

    def compile_ipa(self, ast):
        ret_text = self._t(
            "the {1} sound /{2}/", self._recons_label(ast), ast["ipa"]["ipa"]
        )

        return clean(ret_text)

    def compile_sound_class(self, ast):
        sound_class = ast["sound_class"]["sound_class"]

        ret_text = self._t(
            "some {1} sound of class {2} ({3})",
            self._recons_label(ast),
            sound_class,
            self._t(self.sound_classes[sound_class]["description"]),
        )

        if ast.get("modifier"):
            ret_text = self._t(
                "{1} (changed into {2})", ret_text, self._compile_modifier(ast)
            )

        return clean(ret_text)

    def compile_boundary(self, ast):
        return self._t("a word boundary")

    def compile_empty(self, ast):
        return self._t("no sound")

    def compile_back_ref(self, ast):
        # Using different strings for orders less or equal to three
        idx = int(ast["back_ref"])
        if idx <= 3:
            ret_text = self._t(
                "the {1} {2} matched sound",
                self._recons_label(ast),
                self._t(["first", "second", "third"][idx - 1]),
            )
        else:
            ret_text = self._t(
                "the {1} matched sound of number {2}",
                self._recons_label,
                ast["back_ref"],
            )

        if ast.get("modifier"):
            ret_text = self._t(
                "{1} (changed into {2})", ret_text, self._compile_modifier(ast)
            )

        return clean(ret_text)

    def compile_feature_desc(self, ast):
        descriptors = [
            self._t("not {1}", f["key"])
            if f["value"] in ["false", "-"]
            else f["key"]
            for f in ast["feature_desc"]
        ]

        # Compile and return the textual representation of descriptors
        return self._t(
            "a {1} {2} sound", self._recons_label(ast), ", ".join(descriptors)
        )

    def compile_alternative(self, ast):
        # Alternatives always hold sequences (even if it is a single grapheme,
        # for example, it is a sequence of a single grapheme). As such, we
        # collect the textual description of each alternative as a sequence,
        # before joining the text and returning.
        # NOTE: working around what seems to be a problem in TatSu
        if len(ast["alternative"]) == 1:
            ret_text = self.compile(ast["alternative"][0])
        else:
            descriptors = [
                self.compile(altern) for altern in ast["alternative"]
            ]

            # The texual representation of alternatives is separated by commas,
            # but we add an "or" conjuction to the last item *even* when we
            # only have two alterantives.
            if len(descriptors) == 2:
                ret_text = self._t(
                    "either {1} or {2}",
                    ", ".join(descriptors[:-1]),
                    descriptors[-1],
                )
            else:
                ret_text = self._t(
                    "either {1}, or {2}",
                    ", ".join(descriptors[:-1]),
                    descriptors[-1],
                )

        return ret_text

    def compile_sequence(self, ast):
        segment_texts = [self.compile(segment) for segment in ast["sequence"]]

        # Join the segments in a single string
        if len(segment_texts) == 1:
            ret_text = segment_texts[0]
        elif len(segment_texts) == 2:
            ret_text = self._t(
                "{1} followed by {2}", segment_texts[0], segment_texts[1]
            )
        else:
            ret_text = self._t(", followed by ").join(segment_texts)

        return ret_text

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

        return preceding_text, following_text

    def compile_start(self, ast):
        # Collect `source` and `target` representations
        source = self.compile(ast["source"])
        target = self.compile(ast["target"])

        # Build return text with source and targe (context will be added later,
        # if available)
        if target == self._t("no sound"):
            ret_text = self._t(
                "the source, composed of {1}, is deleted", source
            )
        else:
            ret_text = self._t(
                "the source, composed of {1}, turns into the target, composed of {2}",
                source,
                target,
            )

        # Collect "context" if available (also a sequence)
        preceding, following = self.compile_context(ast)

        if preceding and following:
            ret_text = self._t(
                "{1}, when preceded by {2} and followed by {3}",
                ret_text,
                preceding,
                following,
            )
        elif preceding:
            ret_text = self._t("{1}, when preceded by {2}", ret_text, preceding)
        elif following:
            ret_text = self._t("{1}, when followed by {2}", ret_text, following)

        # Apply language-specific replacements before returning
        for entry in self._replacements[self.lang]:
            ret_text = ret_text.replace(*entry)

        return ret_text
