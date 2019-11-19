# encoding: "utf-8"

"""
Defines class for representing graphically representing an AST with Graphviz.

Note that, by design, this module and its automata does *not* use any
graphviz integration library, but generates graph source code in the
DOT language, optionally also compiling the graph itself with
the installed version of `graphviz`, called as a subprocess.
"""

# Import Python libraries
import pathlib
import subprocess
import tempfile

# Import `alteruphono` modules
from . import compiler

# DOT source code template
_TEMPLATE = """digraph G {
graph [layout="dot",ordering="out",splines="polyline"] ;
%s
%s
{rank=same;%s} ;
{rank=same;%s} ;
}"""


class GraphAutomata(compiler.Compiler):
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

    def __str__(self):
        buf = "nodes: %s;edges: %s" % (self.nodes, self.edges)

        return buf

    def _clear_status(self):
        self.nodes = {}
        self.edges = []

    def _add_node(self, name, label, parent):
        self.nodes[name] = label
        self.edges.append([parent, name])

    def _add_sequence(self, sequence, label):
        # Add `source` nodes and edges
        for idx, segment in enumerate(sequence):
            # Check if the sequence is an expression, returned as a list,
            # or a singleton. Single-item lists, which related to how
            # the grammar and the parser capture the code, are treated as
            # single entry items (which means that the edge will link
            # the `label` to them directly, instead of having an
            # intermediate `expression` node).
            node_name = "%s%i" % (label[0].upper(), idx)

            # Already preparing for grammar changes, singletons are
            # transformed into single-item lists (as they should be returned)
            # by the parser in the future.
            if not isinstance(segment, list):
                segment = [segment]

            # Single-items are added directly; expressions need an
            # intermediate node.
            if len(segment) == 1:
                self._add_node(node_name, segment[0], label)
            else:
                self._add_node(node_name, "alternative", label)
                for alt_idx, alternative in enumerate(segment):
                    self._add_node(
                        "%sa%i" % (node_name, alt_idx), alternative, node_name
                    )

    def dot_source(self):
        """
        Returns the DOT representation of the graph internally determined.
        """

        # Fail if we have no nodes/edges
        if not self.nodes and not self.edges:
            raise ValueError("Nothing to compile (was `.compile() called?`)")

        # Build a list of all nodes
        nodes_str = [
            '\t%s [label="%s"] ;' % (key, value)
            for key, value in self.nodes.items()
        ]

        # Build a list of all edges, taking care of Graphviz ports
        # (e.g. ":s") if they are used
        edges_str = []
        for edge in self.edges:
            source_label = edge[0].split(":", 1)
            if len(source_label) == 1:
                source_label_str = '"%s"' % source_label[0]
            else:
                source_label_str = '"%s":%s' % (
                    source_label[0],
                    source_label[1],
                )

            target_label = edge[1].split(":", 1)
            if len(target_label) == 1:
                target_label_str = '"%s"' % target_label[0]
            else:
                target_label_str = '"%s":%s' % (
                    target_label[0],
                    target_label[1],
                )

            edges_str.append(
                "\t%s -> %s ;" % (source_label_str, target_label_str)
            )

        # List ranks for all segments directly coming from
        # {source,target,context}, and for all alternatives (which should be
        # one level below). We first select all non-high level nodes,
        # and then filter appropriately.
        rank_nodes = [node for node in self.nodes if node[0] in "STC"]
        seg_rank = [node for node in rank_nodes if "a" not in node]
        alt_rank = [node for node in rank_nodes if "a" in node]

        # Build final string
        buf = _TEMPLATE % (
            "\n".join(nodes_str),
            "\n".join(edges_str),
            ";".join(seg_rank),
            ";".join(alt_rank),
        )

        return buf

    def output(self, output_file):
        """
        Generates a visualization by calling the local `graphviz`.

        The filetype will be decided from the extension of the `filename`.
        """

        # Obtain the source and make it writable
        dot_source = self.dot_source()
        dot_source = dot_source.encode("utf-8")

        # Write to a named temporary file so we can call `graphviz`
        handler = tempfile.NamedTemporaryFile()
        handler.write(dot_source)
        handler.flush()

        # Get the filetype from the extension and call graphviz
        suffix = pathlib.PurePosixPath(output_file).suffix
        subprocess.run(
            ["dot", "-T%s" % suffix[1:], "-o", output_file, handler.name],
            check=True,
        )

        # Close the temporary file
        handler.close()

    # Overriden methods

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

    def compile_expression(self, ast):
        return [self.compile(altern) for altern in ast["expression"]]

    def compile_context(self, ast):
        if ast.get("context"):
            return self.compile(ast["context"])

        return None

    def compile_start(self, ast):
        # Clear interval variables, allowing reuse
        self._clear_status()

        # Add nodes for source and target, as well as context if found
        self._add_node("source", "source", "start")
        self._add_node("target", "target", "start")

        # Add `source` nodes and edges
        self._add_sequence(self.compile(ast["source"]), "source")

        # Add `target` nodes and edges
        self._add_sequence(self.compile(ast["target"]), "target")

        # Add `context` nodes and edges, if any
        context = self.compile_context(ast)
        if context:
            self.edges.append(["start", "context"])
            self._add_sequence(context, "context")

        # Add edges for back-references
        for node_name, node_text in self.nodes.items():
            if node_text[0] == "@":
                idx = int(node_text[1:]) - 1
                self.edges.append(["S%i:s" % idx, "%s:s" % node_name])
