# Import `alteruphono` modules
from . import compiler

# TODO: npte on no graphviz dependency
# TODO: accept a string with a description (could be the other transducer)
# TODO: allow writing to file (and maybe even calling graphviz)
# TODO: single function to append new node and its edge
# TODO: draw border
# TODO: add indices?
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

    def _clear_status(self):
        self.nodes = {}
        self.edges = []

    def _add_node(self, name, label, parent):
        self.nodes[name] = label
        self.edges.append([parent, name])

    # TODO: better logic for `label_letter` etc.
    def _add_sequence(self, sequence, label):
        letter = label[0].upper()

        # Add `source` nodes and edges
        for idx, segment in enumerate(sequence):
            # check if it is an list (i.e., an alternative), also
            # considering that the alternative could be a single item
            # TODO: better checking than with isinstnace
            node_name = "%s%i" % (letter, idx)
            if isinstance(segment, list):
                # single items
                if len(segment) == 1:
                    self._add_node(node_name, segment[0], label)
                else:
                    # all items in the alternative
                    self._add_node(node_name, "alternative", label)
                    for alt_idx, alternative in enumerate(segment):
                        self._add_node("%sa%i" % (node_name, alt_idx), alternative, node_name)
            else:
                self._add_node(node_name, segment, label)

    # "Local" methods

    def build_dot(self):
        """
        Returns the DOT representation of the graph internally determined.
        """

        # List all nodes
        nodes_str = [
            '\t%s [label="%s"] ;' % (key, value)
            for key, value in self.nodes.items()
        ]

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

        # List ranks for all segments (alternatives go one level below)
        # (make sure everything is in the same line,
        # especially when back-reference edges are involved)
        # TODO: better selection of alternatives, involves node name
        segment_rank_str = "{rank=same;%s} ;" % ";".join(
            [node for node in self.nodes if node[0] in "STC"
            and "a" not in node]
        )

        alternative_rank_str = "{rank=same;%s}" % ";".join(
            [node for node in self.nodes if node[0] in "STC"
            and "a" in node]
        )

        # Build final string
        buf = """
        digraph G {
            graph [layout="dot",ordering="out",splines="polyline"] ;
            %s
            %s
            %s
            %s
        }""" % (
            "\n".join(nodes_str),
            "\n".join(edges_str),
            segment_rank_str,
            alternative_rank_str,
        )

        return buf

    # Overriden methods

    def compile_ipa(self, ast):
        return "(ipa:%s)" % ast["ipa"]["ipa"]

    # TODO: take list of definitions as well, at least en?
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
        return "[%s]" % ast["feature_desc"]

    def compile_sequence(self, ast):
        return [self.compile(segment) for segment in ast["sequence"]]

    def compile_alternative(self, ast):
        return [self.compile(altern) for altern in ast["alternative"]]

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
        self._add_sequence(self.compile(ast["source"]), "source")

        # Add `target` nodes and edges
        # NOTE: no alternatives here, as it is target
        self._add_sequence(self.compile(ast["target"]), "target")
        # Add `context` nodes and edges, if any
        context = self.compile_contex(ast)
        if context:
            self.edges.append(["start", "context"])
            self._add_sequence(context, "context")

        # Add edges for back-references
        # TODO: proper back-reference notation
        for node_name, node_text in self.nodes.items():
            if node_text[0] == "@":
                idx = int(node_text[1:]) - 1
                self.edges.append(["S%i:s" % idx, "%s:s" % node_name])

        ret = {"s": self.nodes, "e": self.edges}
        #        pprint.pprint(ret)
        return str(ret)
