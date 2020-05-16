"""
Sound Change parser.
"""

# Import Python standard libraries
from collections.abc import Mapping, Iterable
from pathlib import Path

# Import 3rd-party libraries
import arpeggio
from arpeggio.peg import ParserPEG


def json_value(obj, seen=None):
    """
    Return a JSON representation of a value.

    The function accounts for recursive elements.
    """

    def _isiter(item):
        return isinstance(item, Iterable) and not isinstance(item, str)

    if isinstance(obj, Mapping) or _isiter(obj):
        # prevent traversal of recursive structures
        if seen is None:
            seen = set()
        elif id(obj) in seen:
            return "__RECURSIVE__"
        seen.add(id(obj))

    if hasattr(obj, "__json__") and not isinstance(obj, type):
        return obj.__json__()

    # TODO: check original code, would never get here
    if isinstance(obj, Mapping):
        result = {}
        for key, val in obj.items():
            try:
                result[key] = json_value(val, seen)
            except TypeError:
                raise ValueError("Unhashable key?", type(key), str(key))
        return result
    elif _isiter(obj):
        return [json_value(e, seen) for e in obj]
    else:
        return obj


# TODO: implement a __hash__ method
class AST(dict):
    """
    `AST` class for abstract syntax tree manipulation.

    ASTs are here implemented as a custom dictionary that works as a frozen
    one (fields/attributes cannot be changed after initialization, but there
    is a .copy() method that accepts an `update` dictionary) and which can
    be accessed both as dictionary fields (e.g., `ast['grapheme']`) and as
    attributes (e.g., `ast.grapheme`).

    It is a convenient solution for prototyping and experimenting, besides the
    easiness it provides for manipulation during simulations. It might in the
    future be replaced by some standard Python solution, probability data
    classes.

    The implementation extends the one used by the 竜 TatSu library as of
    2020.05.09, and it is licensed under the BSD-3 clause license of
    竜 TatSu.
    """

    _frozen = False

    def __init__(self, *args, **kwargs):
        # Initialize with new data
        super().__init__()
        self.update(*args, **kwargs)

        # Given that the structure is immutable and the serialization is
        # really expansive in terms of computing cycles, compute it once and
        # store it
        self._cache_json = json_value(self)
        self._cache_repr = repr(self._cache_json)
        self._cache_str = str(self._cache_json)

        # Froze the structure
        self._frozen = True

    @property
    def frozen(self):
        """Property informing whether the AST is frozen."""
        return self._frozen

    def copy(self, update=None):
        if update:
            tmp = dict(self)
            tmp.update(update)
            return AST(tmp)

        return self.__copy__()

    def asjson(self):
        """Return the AST as a JSON."""
        return self._cache_json

    def _set(self, key, item_value, force_list=False):
        key = self._safekey(key)
        previous = self.get(key)

        if previous is None and force_list:
            item_value = [item_value]
        elif previous is None:
            pass
        elif isinstance(previous, list):
            item_value = previous + [item_value]
        else:
            item_value = [previous, item_value]

        super().__setitem__(key, item_value)

    def _setlist(self, key, item_value):
        return self._set(key, item_value, force_list=True)

    def __copy__(self):
        return AST(self)

    def __getitem__(self, key):
        if key in self:
            return super().__getitem__(key)

        key = self._safekey(key)
        if key in self:
            return super().__getitem__(key)

    def __setitem__(self, key, item_value):
        self._set(key, item_value)

    def __delitem__(self, key):
        key = self._safekey(key)
        super().__delitem__(key)

    def __setattr__(self, name, item_value):
        if self._frozen and name not in vars(self):
            raise AttributeError(
                f"{type(self).__name__} attributes are fixed. "
                f' Cannot set attribute "{name}".'
            )
        super().__setattr__(name, item_value)

    def __getattr__(self, name):
        key = self._safekey(name)
        if key in self:
            return self[key]
        if name in self:
            return self[name]

        try:
            return super().__getattribute__(name)
        except AttributeError:
            return None

    def __hasattribute__(self, name):
        try:
            super().__getattribute__(name)
        except (TypeError, AttributeError):
            return False
        else:
            return True

    def __reduce__(self):
        return (AST, (), None, None, iter(self.items()))

    def _safekey(self, key):
        while self.__hasattribute__(key):
            key += "_"
        return key

    def _define(self, keys, list_keys=None):
        for key in keys:
            key = self._safekey(key)
            if key not in self:
                super().__setitem__(key, None)

        for key in list_keys or []:
            key = self._safekey(key)
            if key not in self:
                super().__setitem__(key, [])

    def __json__(self):
        return {name: json_value(value) for name, value in self.items()}

    # TODO: could we have a single one?
    def __repr__(self):
        return self._cache_repr

    def __str__(self):
        return self._cache_str


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
            if feature.value == "+":
                positive.append(feature.feature)
            elif feature.value == "-":
                negative.append(feature.feature)

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

        return list(children)

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

        # return the sound class along with any modifier
        if len(children) == 2:
            return AST({"sound_class": children[0], "modifier": children[1]})

        return AST({"sound_class": children[0]})

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
                        "ante": _merge_context(ast.ante, ast.context),
                        "post": _merge_context(
                            ast.post, ast.context, offset_ref=len(ast.ante)
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

    parser = Parser(debug=True)
    value = parser(sys.argv[1])
    print(value)
