"""
Sound Change parser.
"""

# Import Python standard libraries
from collections.abc import Mapping
from pathlib import Path

# Import 3rd-party libraries
import arpeggio
from arpeggio.peg import ParserPEG

# TODO: freeze after initialization and cache representations
class AST(Mapping):
    """
    `AST` class for abstract syntax tree manipulation.
    """

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = None

    def copy(self, update=None):
        d = self._d.copy()
        if update:
            d.update(update)

        return AST(d)

    def __contains__(self, key):
        # TODO: replace all `in` occurrences to call `__getitem__`?
        return key in self._d

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d.get(key, None)

    def __repr__(self):
        return repr(self._d)

    def __str__(self):
        return str(self._d)

    def __hash__(self):
        # It would have been simpler and maybe more obvious to
        # use hash(tuple(sorted(self._d.iteritems()))) from this discussion
        # so far, but this solution is O(n). I don't know what kind of
        # n we are going to run into, but sometimes it's hard to resist the
        # urge to optimize when it will gain improved algorithmic performance.
        if self._hash is None:
            hash_ = 0
            for pair in self.iteritems():
                hash_ ^= hash(pair)
            self._hash = hash_
        return self._hash


# Define a visitor for semantic analysis of the parse tree. The semantic
# operations are mostly obvious, just casting the returned dictionaries
# into our `AST` class and returning a structure with as new nested
# elements as possible.
class SoundChangeVisitor(arpeggio.PTNodeVisitor):
    """
    Visitor for the semantic analysis of parse trees.
    """

    # Don't capture `arrow`s or`slash`es
    def visit_arrow(self, node, children):
        """Define visitor for the `arrow` rule."""
        # pylint: disable=unused-argument,no-self-use,unnecessary-pass

        pass

    def visit_slash(self, node, children):
        """Define visitor for the `slash` rule."""
        # pylint: disable=unused-argument,no-self-use,unnecessary-pass

        pass

    # Feature captures
    def visit_op_feature(self, node, children):
        """Define visitor for the `op_feature` rule."""
        # pylint: disable=unused-argument,no-self-use

        # "+stop", "-voiced", "voiced"
        if len(children) == 1:
            return AST({"feature": children[0], "value": "+"})

        return AST({"feature": children[1], "value": children[0]})

    def visit_feature_val(self, node, children):
        """Define visitor for the `feature_val` rule."""
        # pylint: disable=unused-argument,no-self-use

        # "stop=true", "voiced=false"
        # TODO: correct after updating grammar for multiple/custom values
        if children[2] == "true":
            return AST({"feature": children[0], "value": "+"})
        if children[2] == "false":
            return AST({"feature": children[0], "value": "-"})

        raise ValueError("invalid value")

    def visit_feature_list(self, node, children):
        """Define visitor for the `feature_list` rule."""
        # pylint: disable=unused-argument,no-self-use

        # TODO: write properly, currently without custom
        positive, negative = [], []
        for feature in children:
            if feature["value"] == "+":
                positive.append(feature["feature"])
            elif feature["value"] == "-":
                negative.append(feature["feature"])

        return AST(
            {
                "positive": sorted(positive),
                "negative": sorted(negative),
                "custom": [],
            }
        )

    def visit_modifier(self, node, children):
        """Define visitor for the `modifier` rule."""
        # pylint: disable=unused-argument,no-self-use

        # don't collect square brackets
        return children[1]

    def visit_focus(self, node, children):
        """Define visitor for the `focus` rule."""
        # pylint: disable=unused-argument,no-self-use

        return AST({"focus": node.value})

    def visit_set(self, node, children):
        """Define visitor for the `set` rule."""
        # pylint: disable=unused-argument,no-self-use

        return AST({"set": list(children)})

    def visit_choice(self, node, children):
        """Define visitor for the `choice` rule."""
        # pylint: disable=unused-argument,no-self-use

        if children[0] == "!":
            return AST({"choice": list(children[1:]), "negation": True})

        return AST({"choice": list(children)})

    def visit_boundary(self, node, children):
        """Define visitor for the `boundary` rule."""
        # pylint: disable=unused-argument,no-self-use

        return AST({"boundary": node.value})

    def visit_empty(self, node, children):
        """Define visitor for the `empty` rule."""
        # pylint: disable=unused-argument,no-self-use

        return AST({"empty": node.value})

    def visit_backref(self, node, children):
        """Define visitor for the `backref` rule."""
        # pylint: disable=unused-argument,no-self-use

        # skip the "@" sign and return the index as an integer,
        # along with any modifier; node that we substract one unit
        # as our lists indexed from 1 (unlike Python, from zero)
        if len(children) == 3:  # @ index modifier
            return AST(
                {"backref": int(children[1]) - 1, "modifier": children[2]}
            )

        return AST({"backref": int(children[1]) - 1})

    def visit_sound_class(self, node, children):
        """Define visitor for the `sound_class` rule."""
        # pylint: disable=unused-argument,no-self-use

        # check for negation
        negation = False
        if children[0] == "!":
            negation = True
            children.pop(0)

        # return the sound class along with any modifier
        if len(children) == 2:
            ret = AST(
                {
                    "sound_class": children[0],
                    "modifier": children[1],
                    "negation": negation,
                }
            )
        else:
            ret = AST({"sound_class": children[0], "negation": negation})

        return ret

    def visit_grapheme(self, node, children):
        """Define visitor for the `grapheme` rule."""
        # pylint: disable=unused-argument,no-self-use

        # return the grapheme along with any modifier
        if len(children) == 2:
            return AST({"grapheme": children[0], "modifier": children[1]})

        return AST({"grapheme": children[0]})

    # Sequences -- if calling `rule`, will visit the three bottom, `sequence`
    # is only visited if asked directly
    def visit_sequence(self, node, children):
        """Define visitor for the `sequence` rule."""
        # pylint: disable=unused-argument,no-self-use

        return list(children)

    def visit_ante(self, node, children):
        """Define visitor for the `ante` rule."""
        # pylint: disable=unused-argument,no-self-use

        return {"ante": list(children)}

    def visit_post(self, node, children):
        """Define visitor for the `post` rule."""
        # pylint: disable=unused-argument,no-self-use

        return {"post": list(children)}

    def visit_context(self, node, children):
        """Define visitor for the `context` rule."""
        # pylint: disable=unused-argument,no-self-use

        return {"context": list(children)}

    # Entry point
    def visit_rule(self, node, children):
        """Define visitor for the `rule` rule."""
        # pylint: disable=unused-argument,no-self-use

        # Combine all subsquences, dealing with context optionality
        ret = {}
        for seq in children:
            ret.update(seq)

        return AST(ret)


class Parser:
    """
    Sound Change parser.
    """

    # Holds the real parser, loaded dinamically on first call
    _parser = None

    def __init__(self, root_rule="rule", debug=False):
        self.debug = debug
        self.root_rule = root_rule

    def load_grammar(self):
        """
        Loads and compiles the PEG grammar.
        """

        grammar_path = Path(__file__).parent / "sound_change.ebnf"
        with open(grammar_path.as_posix()) as grammar:
            self._parser = ParserPEG(
                grammar.read(), self.root_rule, ws="\t ", debug=self.debug
            )

    # NOTE: For saving cycles and to maintain the idea of an independent
    # parser, we don't perform text normalization (such as mapping to
    # Unicode NFC form) here; if necessary, it should be performed by
    # the caller.
    def __call__(self, text):
        # Load and compile the grammar if necessary
        if not self._parser:
            self.load_grammar()

        # Parse the tree and visit each node
        ast = arpeggio.visit_parse_tree(
            self._parser.parse(text), SoundChangeVisitor()
        )

        # Perform merging if the rule is the default (and if there is
        # a context).
        # TODO: does it need to be an AST?
        if self.root_rule == "rule":
            if "context" in ast:
                return AST(
                    {
                        "ante": _merge_context(ast["ante"], ast["context"]),
                        "post": _merge_context(
                            ast["post"],
                            ast["context"],
                            offset_ref=len(ast["ante"]),
                        ),
                    }
                )

        return ast


def _merge_context(ast, context, offset_ref=None):
    """
    Merge an `ante` or `post` AST with a `context`.

    The essentials of the function are to add the left context at the
    beginning and the right one at the endself.

    The most important operation is to fix the indexes of back-references, in
    case they are used. This is specified via the `offset_ref` numeric
    variable: if provided, back-references will be positively shifted
    according to it (as we need to know the length of the AST before the
    right context in what we are referring to).
    """
    # pylint: disable=undefined-loop-variable

    # Split at the `focus` symbol of the context, which is mandatory. Note
    # that we don't use a list comprehension, but a loop, in order to
    # break as soon as the focus is found.
    for idx, token in enumerate(context):
        if isinstance(token, AST) and "focus" in token:
            break
    left, right = context[:idx], context[idx + 1 :]

    # cache the length of `left` and of `ast`
    offset_left = len(left)
    offset_ast = offset_left + len(ast)

    # Merge the provided AST with the contextual one
    # TODO: take care of backreferences in alternatives
    merged_ast = []
    for token in ast:
        # `p @2 / a _` --> `a p @3`
        if "backref" in token:
            merged_ast.append(
                token.copy({"backref": token["backref"] + offset_left})
            )
        else:
            merged_ast.append(token)

    # Apply the `offset_ref` if provided, using `offset_ast` otherwise,
    # to build the final mapping. This is mostly responsible for
    # turning `post` into a long series of back-references in most cases,
    # such as in "V s -> @1 z @1 / # p|b r _ t|d", where `post`
    # becomes "@1 @2 @3 @4 z @4 @6"
    if offset_ref:
        # Here we can just fill the backreferences, as there are no modifiers
        merged_ast = (
            [AST({"backref": i}) for i, _ in enumerate(left)]
            + merged_ast
            + [
                AST({"backref": i + offset_left + offset_ref})
                for i, _ in enumerate(right)
            ]
        )
    else:
        merged_ast = left + merged_ast
        for token in right:
            if "backref" in token:
                merged_ast.append(
                    token.copy({"backref": token.backref + offset_ast})
                )
            else:
                merged_ast.append(token)

    return merged_ast


if __name__ == "__main__":
    # pylint: disable=invalid-name
    import sys

    if len(sys.argv) != 2:
        raise ValueError("Should provide the rule and only the rule.")

    debug = False
    parser = Parser(debug=debug)
    value = parser(sys.argv[1])
    print(value)
