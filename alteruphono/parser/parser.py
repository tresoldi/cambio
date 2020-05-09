"""
Sound Change parser.
"""

# Import Python standard libraries
from pathlib import Path

# Import 3rd-party libraries
# TODO: should use traditional instead of clean PEG?
import arpeggio
from arpeggio.cleanpeg import ParserPEG

# Import package
from alteruphono.ast import AST

# TODO: compile a prettified grammar for saving some time on loading?
# TODO: check about debug options
# TODO: should memoize? -- almost surely yes
# TODO: should normalization be applied here?
# TODO: write auxiliary function for updating backrefs in ASTs?





# Define Sound Change Visitor, for visiting the parse tree
# TODO: add feature_val
class SC_Visitor(arpeggio.PTNodeVisitor):
    def visit_op_feature(self, node, children):
        return AST({'feature':children[1], 'value':children[0]})

    def visit_only_feature_key(self, node, children):
        # default to positive
        return AST({'feature':node.value, 'value': '+'})

    def visit_feature_list(self, node, children):
        return list(children)

    def visit_modifier(self, node, children):
        # don't collect square brackets
        return children[1]

    def visit_focus(self, node, children):
        return AST({'focus':node.value})

    def visit_choice(self, node, children):
        return list(children)

    def visit_boundary(self, node, children):
        return AST({'boundary':node.value})

    def visit_empty(self, node, children):
        return AST({'empty':node.value})

    def visit_backref(self, node, children):
        # skip the "@" sign and return the index as an integer,
        # along with any modifier
        # TODO: should the index be made 0-based already here?
        if len(children) == 2:
            return AST({'backref':int(children[1])})
        else:
            return AST({'backref':int(children[1]), 'modifier':children[2]})

    def visit_sound_class(self, node, children):
        # return the sound class along with any modifier
        if len(children) == 2:
            return AST({'sound_class':children[0], 'modifier':children[1]})
        else:
            return AST({'sound_class':children[0]})

    def visit_grapheme(self, node, children):
        # return the grapheme along with any modifier
        if len(children) == 2:
            return AST({'grapheme':children[0], 'modifier':children[1]})
        else:
            return AST({'grapheme':children[0]})

    # Don't capture `arrow`s or`slash`es
    # TODO: can remove?
    def visit_arrow(self, node, children):
        pass
    def visit_slash(self, node, children):
        pass

    # Sequences -- if calling `rule`, will visit the three bottom, `sequence`
    # is only visited if asked directly
    def visit_sequence(self, node, children):
        return list(children)
    def visit_ante(self, node, children):
        return {'ante':list(children)}
    def visit_post(self, node, children):
        return {'post':list(children)}
    def visit_context(self, node, children):
        return {'context': list(children)}

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

        grammar_path = Path(__file__).parent /  "sound_change.ebnf"
        with open(grammar_path.as_posix()) as grammar:
            self._parser = ParserPEG(grammar.read(), self.root_rule, ws='\t ', debug=self.debug)

    def __call__(self, text):
        # Load and compile the grammar if necessary
        if not self._parser:
            self._load_grammar()

        # Parse the tree and visit each node
        ast = arpeggio.visit_parse_tree(self._parser.parse(text), SC_Visitor())

        # Apply rule post-processing if necessary
        # TODO: do more properly, checking if ante/post/context are here
        if self.root_rule == "rule":
            ast = self._post_process(ast)

        return ast

    # TODO: this is only for `rule`? rename
    def _post_process(self, ast):
        """
        Apply post-processing to an AST.
        """

        # The notation with context is necessary to follow the tradition,
        # making adoption and usage easier among linguists, but it makes our
        # processing much harder. Thus, we merge `.ante` and `.post` with the
        # `.context` (if any), already here at parsing stage, taking care of
        # issues such as indexes of back-references.
        # TODO: if the rule has alternatives, sound_classes, or other
        #       profilific rules in `context`, it might be necessary to
        #       perform a more complex merging and add back-references in
        #       `post` to what is matched in `ante`, which could potentially
        #       even mean different ASTs for forward and backward. This
        #       needs further and detailed investigation, or explicit
        #       exclusion of such rules (the user could always have the
        #       profilic rules in `ante` and `post`, manually doing what
        #       would be done here).

        # Just return if there is no context
        if not ast.get("context"):
            return ast

        merged_ast = AST({
            "ante" : _merge_context(ast.ante, ast.context),
            "post" : _merge_context(ast.post, ast.context, offset_ref=len(ast.ante)),
        })

        return merged_ast

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
        if isinstance(token, AST):
            if "focus" in token:
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
            token_dict = dict(token)
            token_dict["backref"] += offset_left
            merged_ast.append(AST(token_dict))
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
            [AST({"backref":i + 1}) for i, _ in enumerate(left)]
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
                token_dict = dict(token)
                token_dict["backref"] += offset_ast
                merged_ast.append(AST(token_dict))
            else:
                merged_ast.append(token)

    return merged_ast

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise ValueError("Should provide the rule and only the rule.")

    p = Parser()
    v = p(sys.argv[1])
    print(v)
