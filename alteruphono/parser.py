"""
Sound change parser.

This module holds the functions, methods, and data for parsing sound
changes from strings. While it was first specified as a formal grammar,
by means of a Parsing Expression Grammar, it is now defined "manually",
mostly using simple string manipulations and regular expressions with
no look-behinds. The decision to move was motivated by the growing
complexity of the grammar that had to hold a mutable set of graphemes
and for the plans of expansion/conversion to different languages, trying
to diminish the dependency on Python.
"""

# Import Python standard libraries
import re

# Defines the regular expression matching ante, post, and context
_RE_ANTE_POST = re.compile(r"^(?P<ante>.+?)(=>|->|>)(?P<post>.+?)$")
_RE_BACKREF = re.compile(r"^@(?P<idx>\d+)(?P<modifier>\[.+\])?$")
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
            if "=" in feature:
                feature_name, feature_value = feature.split("=")
                custom[feature_name] = feature_value
            else:
                positive.append(feature)

    return {"positive": positive, "negative": negative, "custom": custom}


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


# TODO: accept modifier in other types, such as IPA and SC
def _translate(token, phdata):
    """
    Translate an intermediate representation of tokens to a human sequence.
    """

    ret = None

    # Try to match the tokens with what is easier verified with a regex
    backref_match = re.match(_RE_BACKREF, token)
    sc_match = re.match(_RE_SOUNDCLASS, token)
    ipamod_match = re.match(_RE_IPA_MOD, token)

    # Evaluate
    if token == "_":
        ret = {"position": "_"}
    elif token == "#":
        ret = {"boundary": "#"}
    elif token == ".":
        ret = {"syllable": "_"}
    elif token == ":null:":
        ret = {"null": "null"}
    elif "|" in token:
        # If the string includes a vertical bar, it a list of alternatives;
        # alternatives can be pretty much anything, graphemes, sound classes
        #  (with modifiers or not), etc.
        alternatives = [_translate(alt, phdata) for alt in token.split("|")]
        ret = {"alternative": alternatives}
    elif backref_match:
        # Check if it is a back-reference, with optional modifiers
        ret = {
            "back-reference": int(backref_match.group("idx")),
            "modifier": backref_match.group("modifier"),
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
    elif token in phdata["sounds"]:
        # At this point, it should be a grapheme; check if it is a valid one
        ret = {"ipa": token}

    return ret


def _tokens2ast(tokens, phdata):
    """
    Given a list of string tokens, returns an AST
    """

    ast = []
    for token in tokens:
        translated = _translate(token, phdata)
        if not translated:
            raise ValueError("Unable to parse", [token])
        ast.append(translated)

    return ast


def _merge_context(ast, context, offset_ref=None):
    """
    Merge an "ante" or "post" AST with a context.

    The essentials of the operation is to add the left context at the
    beginning and the right one at the end, but additional care must be
    taken. The most important operation is to fix back-references, in
    case it is needed. This is specified via the `offset_ref` numeric
    variable: if provided, back-references will be fixed according to it
    (as we need to know the length of the AST before the right context in
    what we are referring to).
    """

    # if there is no context to merge, just return as it is
    if not context:
        return ast

    # split at the `position` symbol, which is mandatory
    pos_idx = ["position" in token for token in context].index(True)
    left, right = context[:pos_idx], context[pos_idx + 1 :]

    # cache len of left and ast, for the offsetting
    offset_left = len(left)
    offset_ast = offset_left + len(ast)

    # Merge the provided AST with the contextual one; note that we are
    # always making copies here, so to treat the provided ASTs as immutable
    # ones.
    # TODO: move to a separate function? it would also make easier to
    # take care of backreferences in alternatives, currently not supported
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


def parse(rule, phdata):
    """
    Parse a sound change rule.
    """

    # Basic string pre-processing, making logic and regexes easier
    rule = re.sub(r"\s+", " ", rule).strip()

    # Tokenize all parts and collect the tokens in quasi-asts
    ante, post, context = _tokenize_rule(rule)
    ante_ast = _tokens2ast(ante, phdata)
    post_ast = _tokens2ast(post, phdata)
    context_ast = _tokens2ast(context, phdata)

    # context is necessary to follow tradition and to make things simpler to
    # code for linguists, but it actually makes out lives harder
    # join ante and post into single sequenes, taking care of back-references,
    # already here
    # TODO: alternatives/sound classes/etc in context should be mapped
    # to back-reference to `ante` when used in `post`, which likely means
    # different asts for forward and back
    new_ante_ast = _merge_context(ante_ast, context_ast)
    new_post_ast = _merge_context(
        post_ast, context_ast, offset_ref=len(ante_ast)
    )

    return {"ante": new_ante_ast, "post": new_post_ast}
