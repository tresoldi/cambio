"""
Sound Change parser.
"""

# Import Python standard libraries
from pathlib import Path

# Import 3rd-party libraries
import arpeggio
from arpeggio.peg import ParserPEG

# Import package
from alteruphono.ast import AST

# TODO: should memoize? -- almost surely yes
# TODO: should normalization be applied here?
# TODO: do the `feature_parse` into positive/negative/custom already here
# TODO: parser should return a Rule, or at least allow so

# Define a visitor for semantic analysis of the parse tree. The semantic
# operations are mostly obvious, just casting the returned dictionaries
# into our `AST` class and returning a structure with as new nested
# elements as possible.
# TODO: add feature_val
class SC_Visitor(arpeggio.PTNodeVisitor):
    # Don't capture `arrow`s or`slash`es
    def visit_arrow(self, node, children):
        pass

    def visit_slash(self, node, children):
        pass

    # Feature captures
    def visit_op_feature(self, node, children):
        # "+stop", "-voiced"
        return AST({"feature": children[1], "value": children[0]})

    def visit_feature_val(self, node, children):
        # "stop=true", "voiced=false"
        # TODO: correct after updating grammar for multiple values
        if children[2] == "true":
            return AST({"feature": children[0], "value": "+"})
        elif children[2] == "false":
            return AST({"feature": children[0], "value": "-"})
        else:
            raise ValueError("invalid value")

    def visit_only_feature_key(self, node, children):
        # default to positive
        return AST({"feature": node.value, "value": "+"})

    def visit_feature_list(self, node, children):
        return list(children)

    def visit_modifier(self, node, children):
        # don't collect square brackets
        return children[1]

    def visit_focus(self, node, children):
        return AST({"focus": node.value})

    def visit_choice(self, node, children):
        return list(children)

    def visit_boundary(self, node, children):
        return AST({"boundary": node.value})

    def visit_empty(self, node, children):
        return AST({"empty": node.value})

    def visit_backref(self, node, children):
        # skip the "@" sign and return the index as an integer,
        # along with any modifier
        # TODO: should the index be made 0-based already here?
        if len(children) == 3:  # @ index modifier
            return AST({"backref": int(children[1]), "modifier": children[2]})

        return AST({"backref": int(children[1])})

    def visit_sound_class(self, node, children):
        # return the sound class along with any modifier
        if len(children) == 2:
            return AST({"sound_class": children[0], "modifier": children[1]})

        return AST({"sound_class": children[0]})

    def visit_grapheme(self, node, children):
        # return the grapheme along with any modifier
        if len(children) == 2:
            return AST({"grapheme": children[0], "modifier": children[1]})

        return AST({"grapheme": children[0]})

    # Sequences -- if calling `rule`, will visit the three bottom, `sequence`
    # is only visited if asked directly
    def visit_sequence(self, node, children):
        return list(children)

    def visit_ante(self, node, children):
        return {"ante": list(children)}

    def visit_post(self, node, children):
        return {"post": list(children)}

    def visit_context(self, node, children):
        return {"context": list(children)}

    # Entry point
    def visit_rule(self, node, children):
        # Combine all subsquences, dealing with context optionality
        ret = {}
        for seq in children:
            ret.update(seq)

        return AST(ret)


class Parser:
    # Holds the real parser, loaded dinamically on first call
    _parser = None

    def __init__(self, root_rule="rule", debug=False):
        self.debug = debug
        self.root_rule = root_rule

    # TODO: add logging
    def _load_grammar(self):
        """
        Internal function for loading and compiling a grammar.
        """

        grammar_path = Path(__file__).parent / "sound_change.ebnf"
        with open(grammar_path.as_posix()) as grammar:
            self._parser = ParserPEG(
                grammar.read(), self.root_rule, ws="\t ", debug=self.debug
            )

    def __call__(self, text):
        # Load and compile the grammar if necessary
        if not self._parser:
            self._load_grammar()

        # Parse the tree and visit each node
        ast = arpeggio.visit_parse_tree(self._parser.parse(text), SC_Visitor())

        # Perform merging if the rule is the default (and if there is
        # a context).
        # TODO: does it need to be an AST?
        if self.root_rule == "rule":
            if "context" in ast:
                return AST(
                    {
                        "ante": _merge_context(ast.ante, ast.context),
                        "post": _merge_context(
                            ast.post, ast.context, offset_ref=len(ast.ante)
                        ),
                    }
                )

        return ast


# TODO: if the rule has alternatives, sound_classes, or other
#       profilific rules in `context`, it might be necessary to
#       perform a more complex merging and add back-references in
#       `post` to what is matched in `ante`, which could potentially
#       even mean different ASTs for forward and backward. This
#       needs further and detailed investigation, or explicit
#       exclusion of such rules (the user could always have the
#       profilic rules in `ante` and `post`, manually doing what
#       would be done here).
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
                token.copy({"backref": token.backref + offset_left})
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
            [AST({"backref": i + 1}) for i, _ in enumerate(left)]
            + merged_ast
            + [
                AST({"backref": i + 1 + offset_left + offset_ref})
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
    import sys

    if len(sys.argv) != 2:
        raise ValueError("Should provide the rule and only the rule.")

    p = Parser(debug=True)
    v = p(sys.argv[1])
    print(v)
