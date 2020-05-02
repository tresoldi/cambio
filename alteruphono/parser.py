"""
Sound change parser.

This module holds the functions, methods, and data for parsing sound
changes from strings. While it was first specified as a formal grammar,
by means of a Parsing Expression Grammar, it is now implemented "manually",
mostly using simple string manipulations and regular expressions with
no look-behinds. The decision to change was motivated by the growing
complexity of the grammar that had to hold a mutable set of graphemes
and for the plans of expansion/conversion to different languages, trying
to diminish the dependency on Python.
"""

# Import Python standard libraries
import re

# Import package
import alteruphono.utils

# TODO: implement an `__all__`
# TODO: verify why NFC normalization is failing
# TODO: rename `position` to focus?

# Defines the regular expression matching ante, post, and context
_RE_ANTE_POST = re.compile(r"^(?P<ante>.+?)(=>|->|>)(?P<post>.+?)$")
_RE_BACKREF = re.compile(r"^@(?P<idx>\d+)(?P<extra>\[.+\]|\{.+\})?$")
_RE_SOUNDCLASS = re.compile(r"^(?P<sc>[A-Z]+)(?P<modifier>\[.+\])?$")
_RE_IPA_MOD = re.compile(r"^(?P<ipa>.+?)(?P<modifier>\[.+\])?$")


def parse_features(text):
    """
    Parse a list of feature definitions and constraints.

    Constraints can be definied inside optional brackets. Features are
    separated by commas, with optional spaces around them, and have a
    leading plus or minus sign (defaulting to plus).

    Parameters
    ----------
    text: string
        A string with the feature constraints specification

    Returns
    -------
    features : dict
        A dictionary with `positive` features, `negative` features,
        and `custom` features.
    """

    # Remove any brackets from the text that was received and strip it.
    # This allows to generalize this function, so if that it can be used
    # in different contexts (parsing both stuff as "[+fricative]" and
    # "+fricative").
    text = text.replace("[", "")
    text = text.replace("]", "")
    text = text.strip()

    # Analyze all features and build a list of positive and negative
    # features; if a feature is not annotated for positive or negative
    # (i.e., no plus or minus sign), we default to positive.
    # TODO: move the whole thing to regular expressions?
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
            # TODO: check `true` and `false`
            if "=" in feature:
                feature_name, feature_value = feature.split("=")
                custom[feature_name] = feature_value
            else:
                positive.append(feature)

    return {"positive": positive, "negative": negative, "custom": custom}


# TODO: rewrite with a regular expression deciding whether there is a
# context
def _tokenize_rule(rule):
    """
    Internal function for tokenizing a rule.

    At this point, the `rule` string has alredy been preprocessed. Returns
    either the tokens as a list or `None` (in cases such as missing context).
    """

    # We first capture the `context`, if any, and prepare a `ante_post`
    # string for extracting `ante` and `post`
    if " / " in rule:
        ante_post, context = rule.split(" / ")
        context = context.strip().split()
    else:
        ante_post, context = rule, []

    # Extract `ante` and `post` and tokenize them
    match = re.match(_RE_ANTE_POST, ante_post)
    ante = match.group("ante").strip().split()
    post = match.group("post").strip().split()

    return ante, post, context


def _translate(token):
    """
    Translate an intermediate representation of tokens to a human sequence.
    """

    ret = None

    # Try to match the tokens with what is more easily verified with a regex
    backref_match = re.match(_RE_BACKREF, token)
    sc_match = re.match(_RE_SOUNDCLASS, token)
    ipamod_match = re.match(_RE_IPA_MOD, token)

    # Evaluate
    if token == "_":
        ret = {"position": "_"}
    elif token == "#":
        ret = {"boundary": "#"}
    elif token == ".":
        ret = {"syllable": "."}
    elif token == ":null:":
        ret = {"null": "null"}
    elif "|" in token:
        # If the string includes a vertical bar, it a list of alternatives;
        # alternatives can be pretty much anything, graphemes, sound classes
        #  (with modifiers or not), etc.
        ret = {"alternative": [_translate(alt) for alt in token.split("|")]}
    elif backref_match:
        # Check if it is a back-reference, possibly with modifiers or set
        # correspondences
        if not backref_match.group("extra"):
            ret = {"back-reference": int(backref_match.group("idx"))}
        elif backref_match.group("extra")[0] == "[":
            ret = {
                "back-reference": int(backref_match.group("idx")),
                "modifier": backref_match.group("extra"),
            }
        elif backref_match.group("extra")[0] == "{":
            ret = {
                "back-reference": int(backref_match.group("idx")),
                "correspondence": backref_match.group("extra"),
            }
    elif sc_match:
        # Check if it is sound-class, with optional modifier
        ret = {
            "sound_class": sc_match.group("sc"),
            "modifier": sc_match.group("modifier"),
        }
    elif ipamod_match:
        # IPA with modifier
        ret = {
            "ipa": ipamod_match.group("ipa"),
            "modifier": ipamod_match.group("modifier"),
        }
    elif token in globals.SOUNDS:
        # At this point, it should be a grapheme; check if it is a valid one
        ret = {"ipa": token}

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

    The essentials of the function is to add the left context at the
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

    # split at the `position` symbol of the context, which is mandatory
    pos_idx = ["position" in token for token in context].index(True)
    left, right = context[:pos_idx], context[pos_idx + 1 :]

    # cache len of `left` and of `ast`
    offset_left = len(left)
    offset_ast = offset_left + len(ast)

    # Merge the provided AST with the contextual one; note that we are
    # always making copies here, so to treat the provided ASTs as immutable
    # ones.
    # TODO: move to a separate function? it would also make easier to
    # take care of backreferences in alternatives, which are not
    # supported at present
    merged_ast = []
    for token in ast:
        merged_ast.append(dict(token))
        if "back-reference" in token:
            merged_ast[-1]["back-reference"] += offset_left

    if offset_ref:
        merged_ast = (
            [{"back-reference": i + 1} for i, _ in enumerate(left)]
            + merged_ast
            + [
                {"back-reference": i + 1 + offset_left + offset_ref}
                for i, _ in enumerate(right)
            ]
        )
    else:
        merged_ast = left[:] + merged_ast
        for token in right:
            merged_ast.append(dict(token))
            if "back-reference" in token:
                merged_ast[-1]["back-reference"] += offset_ast

    return merged_ast


def parse_rule(rule_text):
    """
    Parse a sound change rule.

    Rules are cleaned with the `_clear_text()` function before parsing,
    which includes removal of multiple and trailing spaces and
    Unicode normalization to the NFC form.

    """

    # Clean and normalize the string containing the rule
    rule_text = alteruphono.utils.clear_text(rule_text)

    # Tokenize all parts and collect the tokens in quasi-asts
    ante_tokens, post_tokens, context_tokens = _tokenize_rule(rule_text)
    ante_ast = _tokens2ast(ante_tokens)
    post_ast = _tokens2ast(post_tokens)
    context_ast = _tokens2ast(context_tokens)

    # The notation with context is necessary to follow the tradition,
    # making adoption and usage easier among linguists, but it makes our
    # processing much harder. Thus, we merge `ante` and `post` with the
    # `context`, if any, already at parsing stage, taking care of
    # issues such as indexes of back-references.
    # TODO: alternatives/sound classes/etc in context should be mapped
    # to back-reference to `ante` when used in `post`, which likely means
    # different asts for forward and back
    merged_ante_ast = _merge_context(ante_ast, context_ast)
    merged_post_ast = _merge_context(
        post_ast, context_ast, offset_ref=len(ante_ast)
    )

    return {"ante": merged_ante_ast, "post": merged_post_ast}
