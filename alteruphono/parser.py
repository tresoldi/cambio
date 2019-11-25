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

# TODO: Decide what will be exported

# Defines the regular expression matching ante, post, and context
# TODO: are we supporting sound classes with modifiers?
_RE_ANTE_POST = re.compile(r"^(?P<ante>.+?)(=>|->|>)(?P<post>.+?)$")
_RE_MODIFIER = re.compile(r"^@(?P<idx>\d+)(?P<modifier>\[.+\])?$")
_RE_SOUNDCLASS = re.compile(r"^(?P<sc>[A-Z]+)(?P<modifier>\[.+\])?$")

# TODO: delete funnction once ready
def _tokenize(text):
    # Sequences at this point have tokens separeted by single spaces,
    # but we might run into cases of capture groups that include
    # multiple segments, such as "(p w|p)". As Go's regexp library does
    # not support lookahead and lookbehind, we need to fix the issue
    # in old-school style: we keep track of whether we are inside a
    # capture group (`in_capture`) and append to the last item if so,
    # instead of just extending the list.
    # Please note that we take of carrying the whitespace over and
    # remove the parentheses, as the split will later happen on the
    # "|" character.
    tokens = []
    in_capture = False
    for token in text.split():
        if in_capture:
            if token[-1] == ")":
                tokens[-1] += " %s" % token[:-1]
                in_capture = False
            else:
                tokens[-1] += " %s" % token
        else:
            if token[0] == "(":
                tokens.append(token[1:])
                in_capture = True
            else:
                tokens.append(token)

    return tokens


# TODO: internal function; at this point, the string has already been
# preprocessed; returns the tokens as lists (or None if no context)
def _tokenize_rule(rule):
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


# TODO: have a parse modifier
# TODO: add a single modifier (which allows to define as wel)

# match tokens (mostly with regex) and build objects
def _translate(token, phdata):
    ret = None

    # TODO: with a walrus operator, this can be moved to the `if`s
    bref_match = re.match(_RE_MODIFIER, token)
    sc_match = re.match(_RE_SOUNDCLASS, token)

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
    elif bref_match:
        # Check if it is a back-reference, with optional modifiers
        ret = {
            "back-reference": int(bref_match.group("idx")),
            "modifier": bref_match.group("modifier"),
        }
    elif sc_match:
        # Check if it is sound-class, with optional modifier
        ret = {
            "sound_class": sc_match.group("sc"),
            "modifier": sc_match.group("modifier"),
        }
    elif token in phdata["sounds"]:
        # at this point it should be a grapheme; check if it is a valid one
        # TODO: accept modifier?
        ret = {"ipa": token}

    return ret


def tokens2ast(tokens, phdata):
    ast = []
    for token in tokens:
        t = _translate(token, phdata)
        if not t:
            raise ValueError("Unable to parse", [t])
        ast.append(t)

    return ast


# TODO: rename `ref_context`, if provided, it means we are replacing all
# contexts with back-references (such as, with forward motion, in
# `post`), and we need to know the length of the ast before the right
# context in the reference itself (in this example, in `ante`)
def _merge_context(ast, context, ref_context=None):
    # if there is no context to merge, just return as it is
    if not context:
        return ast

    # split at the `position` symbol, which is mandatory
    pos_idx = ["position" in token for token in context].index(True)
    left, right = context[:pos_idx], context[pos_idx + 1 :]

    # cache len of left and ast, for the offsetting
    offset_left = len(left)
    offset_ast = offset_left + len(ast)

    # TODO: move to a separate function? it would also make easier to
    # take care of backreferences in alternatives, currently not supported
    # TODO: note that we are making copies here
    # TODO: note about backreferences for contxt when specified
    if ref_context:
        merged = [{"back-reference": i + 1} for i, _ in enumerate(left)]
    else:
        merged = left[:]

    for token in ast:
        merged.append(dict(token))
        if "back-reference" in token:
            merged[-1]["back-reference"] += offset_left

    if ref_context:
        merged += [
            {"back-reference": i + 1 + offset_left + ref_context}
            for i, _ in enumerate(right)
        ]
    else:
        for token in right:
            merged.append(dict(token))
            if "back-reference" in token:
                merged[-1]["back-reference"] += offset_ast

    return merged


def parse(rule, phdata):
    # Basic string pre-processing, making logic and regexes easier
    rule = re.sub("\s+", " ", rule).strip()

    # Tokenize all parts and collect the tokens in quasi-asts
    ante, post, context = _tokenize_rule(rule)
    ante_ast = tokens2ast(ante, phdata)
    post_ast = tokens2ast(post, phdata)
    context_ast = tokens2ast(context, phdata)

    # context is necessary to follow tradition and to make things simpler to
    # code for linguists, but it actually makes out lives harder
    # join ante and post into single sequenes, taking care of back-references,
    # already here
    # TODO: alternatives/sound classes/etc in context should be mapped
    # to back-reference to `ante` when used in `post`, which likely means
    # different asts for forward and back
    new_ante_ast = _merge_context(ante_ast, context_ast)
    new_post_ast = _merge_context(
        post_ast, context_ast, ref_context=len(ante_ast)
    )

    return {"ante": new_ante_ast, "post": new_post_ast}
