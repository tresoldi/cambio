import pprint
import re
import json

# import tatsu
# import soundchange as grammar

# Default sound classes in our system
# TODO: move from string to actual feature descriptor? Have an
#       additional field?
SOUND_CLASS = {
    "A": "affricate",
    "B": "back vowel",
    "C": "consonant",
    "D": "voiced plosive",
    "E": "front vowel",
    "F": "fricative",
    "H": "laryngeal",
    "J": "approximant",
    "K": "velar",
    "L": "liquid",
    "N": "nasal consonant",
    "O": "obstruent",
    "P": "bilabial/labial",
    "Q": "click",
    "R": "resonant (sonorant)",
    "S": "plosive",
    "T": "voiceless plosive",
    "V": "vowel",
    "Z": "continuant",
}


def astseq2text(ast):
    """
    Internal function for translatin an AST sequence, such as source and
    target, to text.
    """

    # Collect the textual representation of each segment
    segment_texts = [ast2text(segment) for segment in ast]

    # Join in a single text; we are currently only adding commas for
    # three or more items.
    if len(segment_texts) == 1:
        ret_text = segment_texts[0]
    elif len(segment_texts) == 2:
        ret_text = "%s followed by %s" % (segment_texts[0], segment_texts[1])
    else:
        ret_text = ", followed by ".join(segment_texts)

    return ret_text


def ast2text(ast):
    print("---------", ast)

    def _recons_label(ast):
        if ast.get("recons"):
            return "reconstructed "

        return ""

    if ast.get("ipa"):
        # If it is a primitive `ipa`, just return the character itself,
        # also checking if it is a reconstruction
        ret_text = "the %ssound /%s/" % (_recons_label(ast), ast["ipa"])

    elif ast.get("sound_class"):
        # Sound classes also have a descriptor
        ret_text = "a %ssound of class %s (%s)" % (
            _recons_label(ast),
            ast["sound_class"],
            SOUND_CLASS[ast["sound_class"]],
        )

    elif ast.get("boundary"):
        ret_text = "a word boundary"

    elif ast.get("feature_desc"):
        descriptors = [
            "not %s" % f["key"] if f["value"] in ["false", "-"] else f["key"]
            for f in ast["feature_desc"]
        ]

        # Compile and return the textual representation of descriptors
        return "a %s%s sound" % (_recons_label(ast), ", ".join(descriptors))

    elif ast.get("sequence"):
        # If it is a `sequence`, collect the textual representation for all
        # segments
        segment_texts = [ast2text(segment) for segment in ast["sequence"]]

        # Join the segments in a single string
        if len(segment_texts) == 1:
            ret_text = segment_texts[0]
        elif len(segment_texts) == 2:
            ret_text = "%s followed by %s" % (
                segment_texts[0],
                segment_texts[1],
            )
        else:
            ret_text = ", followed by ".join(segment_texts)

    elif ast.get("source") and ast.get("target"):
        # Check if we are at first level, that is, if the AST for the `start`
        # symbol was passed. We expect and need at least a `source` and a
        # `target` symbols, which are sequences.

        source = ast2text(ast["source"])
        target = ast2text(ast["target"])

        # Build return text with source and targe (context will be added later,
        # if available)
        ret_text = (
            "the source, composed of %s, turns into the target, composed of %s"
            % (source, target)
        )

        # Collect "context" if available (also a sequence)
        if ast.get("context"):
            # We look for the index of the positional "_" segment in context,
            # so that we can separate preceding and following parts; we
            # build "fake" AST trees as Python dictionaries, making it
            # simpler and using the same .get() method
            is_pos = [
                segment.get("position") is not None
                for segment in ast["context"]["sequence"]
            ]
            idx = is_pos.index(True)

            preceding = {"sequence": ast["context"]["sequence"][:idx]}
            following = {"sequence": ast["context"]["sequence"][idx + 1 :]}

            if preceding["sequence"] and following["sequence"]:
                context = "preceded by %s and followed by %s" % (
                    ast2text(preceding),
                    ast2text(following),
                )
            elif preceding["sequence"]:
                context = "preceded by %s" % ast2text(preceding)
            else:
                context = "followed by %s" % ast2text(following)

            ret_text = "%s, when %s" % (ret_text, context)

    # Single return point for the entire function
    return ret_text


def OLDast2text(ast, profile=None):
    """
    Return a textual description of a sound change in AST format.

    In most cases, this function will call itself recursively times, building
    the textual representation for lower-level entries, down to terminals,
    which are combined in a single textual representation.
    """

    # First step: check if we are at the first level (i.e., "start" symbol in
    # the grammar), which might involve additional textual arrangement than
    # just concatenating the primitives, by looking for a "source" key in the
    # provided abstract syntax tree
    if "source" in ast:
        # TODO: implement different strings patterns, such as deletion (zero
        #       phoneme), mapping, etc.

        # Collect "source" and "target", which are sequences.
        source = _ast_sequence2text(ast["source"])
        target = _ast_sequence2text(ast["target"])

        # Collect "context" if available, also a sequence
        if ast["context"]:
            # We look for the index of the positional "_" segment in context,
            # so that we can separate preceding and following parts
            # NOTE: not working when there is only one segment which is an
            #       alternative (such as in "/ {# _, _#}"), which is
            #       currently throwing an exception.
            try:
                is_pos = ["position" in segment for segment in ast["context"]]
                idx = is_pos.index(True)

                preceding = ast["context"][:idx]
                following = ast["context"][idx + 1 :]
                preceding_str = _ast_sequence2text(preceding)
                following_str = _ast_sequence2text(following)

                if preceding and following:
                    context = "preceded by %s and followed by %s" % (
                        preceding_str,
                        following_str,
                    )
                elif preceding:
                    context = "preceded by %s" % preceding_str
                else:
                    context = "followed by %s" % following_str

            except:
                context = "the context is %s" % _ast_sequence2text(
                    ast["context"]
                )
        else:
            context = None

        # build return text, adding the context if available
        ret_text = (
            "the source, composed of %s, turns into the target, composed of %s"
            % (source, target)
        )
        if context:
            ret_text = "%s, when %s" % (ret_text, context)

        return ret_text

    # Third step: the AST contain some primitive; check which type by
    # looking for keys/values and return the appropriate textual
    # representation.
    if ast.has_key("ipa"):
        if ast.get("recons", None):
            recons_label = "reconstructed "
        else:
            recons_label = ""

        return "the %ssound /%s/" % (recons_label, ast["ipa"])

    elif "sound_class" in ast:
        if ast.get("recons", None):
            recons_label = "reconstructed "
        else:
            recons_label = ""

        return "a %ssound of class %s (%s)" % (
            recons_label,
            ast["sound_class"],
            SOUND_CLASS[ast["sound_class"]],
        )

    elif "feature_desc" in ast:
        # The generated texts and the implied logics are different in case of
        # single entries (such as "[+voiced]"), returned by the parser
        # as a single AST object, and list of entries (such as
        # "[voiced,plosive]"), returned by the parser as a list of AST object
        # (i.e., single features are *not* returned as lists of one element).
        if not isinstance(ast["feature_desc"], list):
            descriptors = [
                "not %s" % ast["feature_desc"]["key"]
                if ast["feature_desc"]["value"] in ["false", "-"]
                else ast["feature_desc"]["key"]
            ]
        else:
            descriptors = [
                "not %s" % f["key"]
                if f["value"] in ["false", "-"]
                else f["key"]
                for f in ast["feature_desc"]
            ]

        # add information on reconstruction
        if ast.get("recons", None):
            recons_label = "reconstructed "
        else:
            recons_label = ""

        # Compile and return the textual representation of descriptors
        return "a %s%s sound" % (recons_label, ", ".join(descriptors))

    elif "alternative" in ast:
        # Alternatives always hold sequences (even if it is a single grapheme,
        # for example, it is a sequence of a single grapheme). As such, we
        # collect the textual description of each alternative as a sequence,
        # before joining the text and returning.
        descriptors = [
            _ast_sequence2text(altern) for altern in ast["alternative"]
        ]

        # The texual representation of alternatives is separated by commas,
        # but we add an "or" conjuction to the last item *even* when we
        # only have two alterantives.
        ret_text = "either %s, or %s" % (
            ", ".join(descriptors[:-1]),
            descriptors[-1],
        )

        return ret_text

    elif "back_ref" in ast:
        # get text from the index
        idx = ast["back_ref"]
        if idx == "1":
            label = "first"
        elif idx == "2":
            label = "second"
        elif idx == "3":
            label = "third"
        else:
            label = "%sth" % idx

        # add information on reconstruction
        if ast.get("recons", None):
            recons_label = "reconstructed "
        else:
            recons_label = ""

        # add information on the modifier, if provided
        if ast["modifier"]:
            mod_text = " (changed into %s)" % ast2text(ast["modifier"])
        else:
            mod_text = ""

        return "the %s%s matched sound%s" % (recons_label, label, mod_text)

    elif "null" in ast:
        # NOTE: this is mostly for mappings, as full deletion should be
        # treated at the sequence level
        return "no sound"

    elif "position" in ast:
        # NOTE: should not be called in most cases, as it is only used to separate the
        #       "preceded" and "suceed" parts
        return "the matching sequence"  # [position]

    elif "boundary" in ast:
        return "a word boundary"

    # print("====", ast)

    return


def test():
    # First round of tests with data not as ASTs but dictionaries
    TESTS = [
        # Test ipa characters
        [{"ipa": "p"}, "the sound /p/"],
        [{"ipa": "ts"}, "the sound /ts/"],
        # test sound classes
        [{"sound_class": "H"}, "a sound of class H (laryngeal)"],
        # test feature description with different numbers of features
        [
            {"feature_desc": [{"key": "voiced", "value": "true"}]},
            "a voiced sound",
        ],
        [
            {"feature_desc": [{"key": "voiced", "value": "false"}]},
            "a not voiced sound",
        ],
        [
            {
                "feature_desc": [
                    {"key": "voiced", "value": "true"},
                    {"key": "plosive", "value": "false"},
                ]
            },
            "a voiced, not plosive sound",
        ],
        # test alterantives with different numbers of alternatives
        [
            {"alternative": [[{"ipa": "p"}], [{"ipa": "b"}]]},
            "either the sound /p/, or the sound /b/",
        ],
        [
            {"alternative": [[{"ipa": "p"}], [{"ipa": "b"}], [{"ipa": "t"}]]},
            "either the sound /p/, the sound /b/, or the sound /t/",
        ],
        # test back reference with and without modification
        [{"back_ref": "2", "modifier": None}, "the second matched sound"],
        [
            {
                "back_ref": "2",
                "modifier": {"feature_desc": [{"key": "voiced", "value": "+"}]},
            },
            "the second matched sound (changed into a voiced sound)",
        ],
        # test extra symbols
        [{"null": "0"}, "no sound"],
        [{"position": "_"}, "the matching sequence"],
        [{"boundary": "#"}, "a word boundary"],
    ]

    for test in TESTS:
        ast, expected = test
        result = ast2text(ast)

        out = "%s -> '%s'... " % (str(ast), expected)
        if expected == result:
            out = "%s OK" % out
        else:
            out = "%s FAIL ('%s')" % (out, result)
        print(out)
