import pprint
import re
import json
from os import path
import csv
from collections import defaultdict

# alteruphono stuff
from . import utils


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
        return NotImplemented

    def compile_sound_class(self, ast):
        return NotImplemented

    def compile_boundary(self, ast):
        return NotImplemented

    def compile_empty(self, ast):
        return NotImplemented

    def compile_back_ref(self, ast):
        return NotImplemented

    def compile_feature_desc(self, ast):
        return NotImplemented

    def compile_alternative(self, ast):
        return NotImplemented

    def compile_sequence(self, ast):
        return NotImplemented

    def compile_context(self, ast):
        """
        The method returns a tuple of two variables, the first for the
        context preceding the position and the second for the one
        following it.
        """

        return NotImplemented

    def compile_start(self, ast):
        return NotImplemented


class Translate(Compiler):
    def __init__(self, sound_classes, lang, debug=False, **kwargs):
        self.sound_classes = sound_classes
        self.lang = lang
        self.debug = debug

        # load the default translations and replacements
        transfile = kwargs.get(
            "transfile", path.join(utils._RESOURCE_DIR, "translations.tsv")
        )
        replfile = kwargs.get(
            "replfile",
            path.join(utils._RESOURCE_DIR, "translation_replacements.tsv"),
        )

        self._gettext = {}
        with open(transfile) as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                ref = row.pop("ref")
                self._gettext[ref] = row

        self._replacements = defaultdict(list)
        with open(replfile) as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                self._replacements[row["language"]].append(
                    [row["source"], row["target"]]
                )

    # Translations
    def _t(self, text, *args):
        # Get translation and make argument replacement in the correct order
        translation = self._gettext[text].get(self.lang, text)
        for idx, arg in enumerate(args):
            translation = translation.replace("{%i}" % (idx + 1), arg)

        return translation

    # "Local" methods

    def _compile_modifier(self, ast):
        return self.compile(ast["modifier"])

    def _recons_label(self, ast):
        if ast.get("recons"):
            return self._t("reconstructed")

        return ""

    def _clean(self, text):
        return re.sub("\s+", " ", text).strip()

    # Overriden methods

    def compile_ipa(self, ast):
        ret_text = self._t(
            "the {1} sound /{2}/", self._recons_label(ast), ast["ipa"]["ipa"]
        )

        return self._clean(ret_text)

    def compile_sound_class(self, ast):
        # TODO: use resource sound classes, possibly passed as argument
        # TODO: language specific sound class
        sound_class = ast["sound_class"]["sound_class"]

        ret_text = self._t(
            "some {1} sound of class {2} ({3})",
            self._recons_label(ast),
            sound_class,
            self._t(self.sound_classes[sound_class]),
        )

        if ast.get("modifier"):
            ret_text = self._t(
                "{1} (changed into {2})", ret_text, self._compile_modifier(ast)
            )

        return self._clean(ret_text)

    def compile_boundary(self, ast):
        return self._t("a word boundary")

    def compile_empty(self, ast):
        return self._t("no sound")

    def compile_back_ref(self, ast):
        # Using different strings for orders less or equal to three
        idx = int(ast["back_ref"])
        if idx <= 3:
            ret_text = self._t(
                "the {1} {2} matched sound",
                self._recons_label(ast),
                self._t(["first", "second", "third"][idx - 1]),
            )
        else:
            ret_text = self._t(
                "the {1} matched sound of number {2}",
                self._recons_label,
                ast["back_ref"],
            )

        if ast.get("modifier"):
            ret_text = self._t(
                "{1} (changed into {2})", ret_text, self._compile_modifier(ast)
            )

        return self._clean(ret_text)

    def compile_feature_desc(self, ast):
        descriptors = [
            self._t("not {1}", f["key"])
            if f["value"] in ["false", "-"]
            else f["key"]
            for f in ast["feature_desc"]
        ]

        # Compile and return the textual representation of descriptors
        return "a {1} {2} sound" % (
            self._recons_label(ast),
            ", ".join(descriptors),
        )

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
                ret_text = self._t(
                    "either {1} or {2}",
                    ", ".join(descriptors[:-1]),
                    descriptors[-1],
                )
            else:
                ret_text = self._t(
                    "either {1}, or {2}",
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
            ret_text = self._t(
                "{1} followed by {2}", segment_texts[0], segment_texts[1]
            )
        else:
            ret_text = self._t(", followed by ").join(segment_texts)

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
        if target == self._t("no sound"):
            ret_text = self._t(
                "the source, composed of {1}, is deleted", source
            )
        else:
            ret_text = self._t(
                "the source, composed of {1}, turns into the target, composed of {2}",
                source,
                target,
            )

        # Collect "context" if available (also a sequence)
        preceding, following = self.compile_context(ast)

        if preceding and following:
            ret_text = self._t(
                "{1}, when preceded by {2} and followed by {3}",
                ret_text,
                preceding,
                following,
            )
        elif preceding:
            ret_text = self._t("{1}, when preceded by {2}", ret_text, preceding)
        elif following:
            ret_text = self._t("{1}, when followed by {2}", ret_text, following)

        # Apply language-specific replacements before returning
        for entry in self._replacements[self.lang]:
            ret_text = ret_text.replace(*entry)

        return ret_text
