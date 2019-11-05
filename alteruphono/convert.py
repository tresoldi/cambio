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


class Compiler:
    def __init__(self, debug=False):
        self.debug = debug

    def compile(self, ast):
        if self.debug:
            print("---------", ast)

        if ast.get("ipa"):
            ret = self.compile_ipa(ast)
        elif ast.get("sound_class"):
            ret = self.compile_sound_class(ast)
        elif ast.get("boundary"):
            ret = self.compile_boundary(ast)
        elif ast.get("empty"):
            ret = self.compile_empty(ast)
        elif ast.get("back_ref"):
            ret = self.compile_back_ref(ast)
        elif ast.get("feature_desc"):
            ret = self.compile_feature_desc(ast)
        elif ast.get("alternative"):
            ret = self.compile_alternative(ast)
        elif ast.get("sequence"):
            ret = self.compile_sequence(ast)
        elif ast.get("source") and ast.get("target"):
            ret = self.compile_start(ast)

        # Single return point for the entire function
        return ret

    def compile_ipa(self, ast):
        return None

    def compile_sound_class(self, ast):
        return None

    def compile_boundary(self, ast):
        return None

    def compile_empty(self, ast):
        return None

    def compile_back_ref(self, ast):
        return None

    def compile_feature_desc(self, ast):
        return None

    def compile_alternative(self, ast):
        return None

    def compile_sequence(self, ast):
        return None

    def compile_context(self, ast):
        """
        The method returns a tuple of two variables, the first for the
        context preceding the position and the second for the one
        following it.
        """

        return None, None

    def compile_start(self, ast):
        return None


#################


def _clean(text):
    return re.sub("\s+", " ", text)


def _recons_label(ast):
    """
    Returns the representation for the `recons`truction flag.
    """

    if ast.get("recons"):
        return "reconstructed"

    return ""


# TODO: call the proper function when implemented
def _modifier_label(ast):
    """
    Returns the representation for a modifier (feature set).
    """

    return ast2text(ast["modifier"])


class English(Compiler):
    def compile_ipa(self, ast):
        return _clean(
            "the %s sound /%s/" % (_recons_label(ast), ast["ipa"]["ipa"])
        )

    def compile_sound_class(self, ast):
        # TODO: use resource sound classes, possibly passed as argument

        sound_class = ast["sound_class"]["sound_class"]

        ret_text = "some %s sound of class %s (%s)" % (
            _recons_label(ast),
            sound_class,
            SOUND_CLASS[sound_class],
        )

        if ast.get("modifier"):
            ret_text = "%s changed into %s" % _modifier_label(ast)

        return _clean(ret_text)

    def compile_boundary(self, ast):
        return "a word boundary"

    def compile_empty(self, ast):
        return "no sound"

    def compile_back_ref(self, ast):
        # Build text from index (note that it is captured as strings)
        idx = ast["back_ref"]
        if idx == "1":
            idx_label = "first"
        elif idx == "2":
            idx_label = "second"
        elif idx == "3":
            idx_label = "third"
        else:
            idx_label = "%sth" % idx

        ret_text = "the %s %s matched sound" % (_recons_label(ast), idx_label)

        if ast.get("modifier"):
            ret_text = "%s changed into %s" % _modifier_label(ast)

        return _clean(ret_text)

    def compile_feature_desc(self, ast):
        descriptors = [
            "not %s" % f["key"] if f["value"] in ["false", "-"] else f["key"]
            for f in ast["feature_desc"]
        ]

        # Compile and return the textual representation of descriptors
        return "a %s %s sound" % (_recons_label(ast), ", ".join(descriptors))

    def compile_alternative(self, ast):
        # Alternatives always hold sequences (even if it is a single grapheme,
        # for example, it is a sequence of a single grapheme). As such, we
        # collect the textual description of each alternative as a sequence,
        # before joining the text and returning.
        # NOTE: working around what seems to be a problem in TatSu
        if len(ast["alternative"]) == 1:
            ret_text = self.compile(ast["alternative"][0])
        else:
            descriptors = [
                self.compile(altern) for altern in ast["alternative"]
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

        return ret_text

    def compile_sequence(self, ast):
        segment_texts = [self.compile(segment) for segment in ast["sequence"]]

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

        return ret_text

    def compile_context(self, ast):
        preceding_text, following_text = None, None

        if ast.get("context"):
            # We first look for the index of the positional "_" segment in
            # context, so that we can separate preceding and following parts;
            # we build "fake" AST trees as Python dictionaries, making it
            # simpler and using the same .get() method
            idx = [
                segment.get("position") is not None
                for segment in ast["context"]["sequence"]
            ].index(True)

            preceding = {"sequence": ast["context"]["sequence"][:idx]}
            following = {"sequence": ast["context"]["sequence"][idx + 1 :]}

            # TODO: call sequence directly?
            if preceding["sequence"]:
                preceding_text = self.compile(preceding)
            if following["sequence"]:
                following_text = self.compile(following)

        return preceding_text, following_text

    def compile_start(self, ast):
        # Collect `source` and `target` representations
        # TODO: call directly sequence?
        source = self.compile(ast["source"])
        target = self.compile(ast["target"])

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
        preceding, following = self.compile_context(ast)

        if preceding and following:
            ret_text = "%s, when preceded by %s and followed by %s" % (
                ret_text,
                preceding,
                following,
            )
        elif preceding:
            ret_text = "%s, when preceded by %s" % (ret_text, preceding)
        elif following:
            ret_text = "%s, when followed by %s" % (ret_text, following)

        return ret_text
