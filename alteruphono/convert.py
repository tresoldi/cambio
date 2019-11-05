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


def ast2text(ast, debug):
    if debug:
        print("---------", ast)

    def _recons_label(ast):
        if ast.get("recons"):
            return "reconstructed "

        return ""

    if ast.get("ipa"):
        # If it is a primitive `ipa`, just return the character itself,
        # also checking if it is a reconstruction
        ret_text = "the %ssound /%s/" % (_recons_label(ast), ast["ipa"]["ipa"])

    elif ast.get("sound_class"):
        # Sound classes also have a descriptor
        ret_text = "a %ssound of class %s (%s)" % (
            _recons_label(ast),
            ast["sound_class"]["sound_class"],
            SOUND_CLASS[ast["sound_class"]["sound_class"]],
        )

        # add information on the modifier, if provided
        # TODO: same code as backref
        if ast["modifier"]:
            mod_text = " (changed into %s)" % ast2text(ast["modifier"])
        else:
            mod_text = ""

        ret_text = "%s %s" % (ret_text, mod_text)

    elif ast.get("boundary"):
        ret_text = "a word boundary"

    elif ast.get("empty"):
        # NOTE: more complex syntax such as "is deleted" must be handler
        # at a higher level
        ret_text = "no sound"

    elif ast.get("back_ref"):
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

        ret_text = "the %s%s matched sound%s" % (recons_label, label, mod_text)

    elif ast.get("feature_desc"):
        descriptors = [
            "not %s" % f["key"] if f["value"] in ["false", "-"] else f["key"]
            for f in ast["feature_desc"]
        ]

        # Compile and return the textual representation of descriptors
        return "a %s%s sound" % (_recons_label(ast), ", ".join(descriptors))

    elif ast.get("alternative"):
        # Alternatives always hold sequences (even if it is a single grapheme,
        # for example, it is a sequence of a single grapheme). As such, we
        # collect the textual description of each alternative as a sequence,
        # before joining the text and returning.
        # NOTE: working around what seems to be a problem in TatSu
        if len(ast["alternative"]) == 1:
            ret_text = ast2text(ast["alternative"][0], debug)
        else:
            descriptors = [
                ast2text(altern, debug) for altern in ast["alternative"]
            ]

            # The texual representation of alternatives is separated by commas,
            # but we add an "or" conjuction to the last item *even* when we
            # only have two alterantives.
            if len(descriptors) == 2:
                ret_text = "either %s or %s" % (
                    ", ".join(descriptors[:-1]),
                    descriptors[-1],
                )
            else:
                ret_text = "either %s, or %s" % (
                    ", ".join(descriptors[:-1]),
                    descriptors[-1],
                )

    elif ast.get("sequence"):
        # If it is a `sequence`, collect the textual representation for all
        # segments
        segment_texts = [
            ast2text(segment, debug) for segment in ast["sequence"]
        ]

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

        source = ast2text(ast["source"], debug)
        target = ast2text(ast["target"], debug)

        # Build return text with source and targe (context will be added later,
        # if available)
        if target == "no sound":
            ret_text = "the source, composed of %s, is deleted" % source
        else:
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
                ret_text = (
                    "%s, when preceding %s and following %s"
                    % (
                        ret_text,
                        ast2text(preceding, debug),
                        ast2text(following, debug),
                    )
                )
            elif preceding["sequence"]:
                ret_text = "%s, when preceding %s" % (
                    ret_text,
                    ast2text(preceding, debug),
                )
            else:
                ret_text = "%s, when following by %s" % (
                    ret_text,
                    ast2text(following, debug),
                )

    # Single return point for the entire function
    return ret_text
