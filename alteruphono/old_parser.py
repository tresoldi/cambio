"""
Sound change parser.

This module holds the functions, methods, and data for parsing sound
changes from strings. While it was first specified as a formal grammar,
by means of a Parsing Expression Grammar, it is now implemented "manually",
mostly using simple string manipulations and regular expressions with
no look-behinds. The decision to change was motivated by the growing
complexity of the grammar that had to hold a mutable set of graphemes
and for the plans of expansion/conversion to different programming
languages, trying to diminish the dependency on Python.
"""

# Import Python standard libraries
import re

# Import package
import alteruphono.utils
from alteruphono.ast import Features
from alteruphono.ast import TokenAlternative
from alteruphono.ast import TokenBackRef
from alteruphono.ast import TokenBoundary
from alteruphono.ast import TokenFocus
from alteruphono.ast import TokenIPA
from alteruphono.ast import TokenNull
from alteruphono.ast import TokenSoundClass
from alteruphono.ast import TokenSylBreak

# Defines the regular expression matching ante, post, and context
_RE_ANTE_POST = re.compile(r"^(?P<ante>.+?)(=>|->|>)(?P<post>.+?)$")
_RE_BACKREF = re.compile(r"^@(?P<idx>\d+)(?P<extra>\[.+\]|\{.+\})?$")
_RE_SOUNDCLASS = re.compile(r"^(?P<sc>[A-Z]+)(?P<modifier>\[.+\])?$")
_RE_IPA_MOD = re.compile(r"^(?P<ipa>.+?)(?P<modifier>\[.+\])?$")


def parse_features(text):
    """
    Parse a string with feature definitions.

    Feature definition strings are composed of one or more features names,
    separated by a comma, each with an optional value (defaulting to
    "positive"). Positive and negative are indicated by preceding "+" and
    "-" operators, respectively. Custom string values are expressed with the
    "key=value" notation.

    A rather complex example of a feature definition is
    `[feat1,-feat2,feat3=value,+feat4]`, returning "feat1" and "feat4"
    as positive features, "feat2" as a negative feature, and the
    custom "feat3" feature with value "value".

    Parameters
    ----------
    text: string
        A feature definition string.

    Returns
    -------
    features : Features
        A `Features` object, with attributes `.positive` (a list of strings),
        `negative` (a list of strings), and `custom` (a dictionary with
        strings as keys and strings as values).
    """

    # Clear text
    text = alteruphono.utils.clear_text(text)

    # Remove any brackets from the text that was received and strip it.
    # This allows to generalize this function, so if that it can be used
    # in different contexts (parsing both stuff as "[+fricative]" and
    # "+fricative").
    text = text.replace("[", "")
    text = text.replace("]", "")

    # Analyze all features and build a list of positive and negative
    # features; if a feature is not annotated for positive or negative
    # (i.e., no plus or minus sign), we default to positive.
    # TODO: rewrite logic with regular expressions
    positive = []
    negative = []
    custom = {}
    for feature in text.split(","):
        # Strip once more, as the user might add spaces next to the commas
        feature = feature.strip()

        # Obtain the positivity/negativity of the feature
        if feature[0] == "-":
            negative.append(feature[1:])
        elif feature[0] == "+":
            positive.append(feature[1:])
        else:
            # If there is no custom value (equal sign), assume it is a positive
            # feature; otherwise, just store in `custom`.
            # TODO: check "true" and "false" strings as well
            if "=" in feature:
                feature_name, feature_value = feature.split("=")
                custom[feature_name] = feature_value
            else:
                positive.append(feature)

    return Features(sorted(positive), sorted(negative), custom)


def _translate(text):
    """
    Translate a string sequence to an AST token.
    """

    ret = None

    # Try to match the text with what is more easily verified with a regex
    backref_match = re.match(_RE_BACKREF, text)
    sc_match = re.match(_RE_SOUNDCLASS, text)
    ipamod_match = re.match(_RE_IPA_MOD, text)

    # Evaluate
    if text == "_":
        ret = TokenFocus()
    elif text == "#":
        ret = TokenBoundary()
    elif text == ".":
        ret = TokenSylBreak()
    elif text == ":null:":
        ret = TokenNull()
    elif "|" in text:
        # If the string includes a vertical bar, it a list of alternatives;
        # alternatives can be pretty much anything, graphemes, sound classes
        #  (with modifiers or not), etc.
        alternative = [_translate(alt) for alt in text.split("|")]
        ret = TokenAlternative(alternative)
    elif backref_match:
        # Check if it is a back-reference, possibly with modifiers or set
        # correspondences
        index = int(backref_match.group("idx"))

        if not backref_match.group("extra"):
            modifier = None
            correspondence = None
        else:
            if backref_match.group("extra")[0] == "[":
                modifier = backref_match.group("extra")
                correspondence = None
            elif backref_match.group("extra")[0] == "{":
                modifier = None
                correspondence = backref_match.group("extra")

        ret = TokenBackRef(index, modifier, correspondence)
    elif sc_match:
        ret = TokenSoundClass(sc_match.group("sc"), sc_match.group("modifier"))
    elif ipamod_match:
        # IPA with modifier
        ret = TokenIPA(
            ipamod_match.group("ipa"), ipamod_match.group("modifier")
        )

    return ret


def _tokens2ast(tokens):
    """
    Given a list of string tokens, returns an AST
    """

    ast = []
    for token in tokens:
        translated = _translate(token)
        if not translated:
            raise ValueError("Unable to parse", [token])
        ast.append(translated)

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

    # if there is no context to merge, just return as it is
    if not context:
        return ast

    # split at the `focus` symbol of the context, which is mandatory
    focus_idx = [token.toktype == "focus" for token in context].index(True)
    left, right = context[:focus_idx], context[focus_idx + 1 :]

    # cache the length of `left` and of `ast`
    offset_left = len(left)
    offset_ast = offset_left + len(ast)

    # Merge the provided AST with the contextual one
    # TODO: take care of backreferences in alternatives
    merged_ast = []
    for token in ast:
        # `p @2 / a _` --> `a p @3`
        merged_ast.append(token)
        if token.toktype == "backref":
            merged_ast[-1].index += offset_left

    # Apply the `offset_ref` if provided, using `offset_ast` otherwise
    if offset_ref:
        merged_ast = (
            [TokenBackRef(i + 1) for i, _ in enumerate(left)]
            + merged_ast
            + [
                TokenBackRef(i + 1 + offset_left + offset_ref)
                for i, _ in enumerate(right)
            ]
        )
    else:
        merged_ast = left[:] + merged_ast
        for token in right:
            merged_ast.append(token)
            if token.toktype == "backref":
                merged_ast[-1].index += offset_ast

    return merged_ast


# TODO: add output with __repr__/__str__, so we can serialize
# TODO: add __eq__?
class Rule:
    def __init__(self, rule_text=None):
        # Initialize `_ante` and `_post` properties; these are intended to
        # be internal and accessed with dot notation via .__getattr__()
        self._ante = None
        self._post = None

        # If a `rule_text` was provided, store it for reference and parse
        self._source = None
        if rule_text:
            self._source = rule_text
            self.parse(rule_text)

    def parse(self, rule_text):
        """
        Parse a sound change rule.

        Rules are cleaned with the `_clear_text()` function before parsing,
        which includes removal of multiple and trailing spaces and
        Unicode normalization to the NFC form.
        """

        # Clean and normalize the string containing the rule
        rule_text = alteruphono.utils.clear_text(rule_text)

        # Tokenize all parts and collect the tokens in quasi-asts
        # TODO: replace initial logic with regex
        if " / " in rule_text:
            ante_post, context = rule_text.split(" / ")
            context_tokens = context.strip()
        else:
            ante_post, context_tokens = rule_text, ""

        # Extract `ante` and `post` and tokenize them
        match = re.match(_RE_ANTE_POST, ante_post)
        if not match:
            raise alteruphono.utils.AlteruPhonoError("Unable to parse rule.")
        ante_tokens = match.group("ante").strip()
        post_tokens = match.group("post").strip()

        ante_ast = _tokens2ast(ante_tokens.split())
        post_ast = _tokens2ast(post_tokens.split())
        context_ast = _tokens2ast(context_tokens.split())

        # The notation with context is necessary to follow the tradition,
        # making adoption and usage easier among linguists, but it makes our
        # processing much harder. Thus, we merge `ante` and `post` with the
        # `context` (if any), already here at parsing stage, taking care of
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
        self.ante = _merge_context(ante_ast, context_ast)
        self.post = _merge_context(
            post_ast, context_ast, offset_ref=len(ante_ast)
        )
