#!/usr/bin/env python3
# encoding: utf-8

"""
test_compilers
==============

Tests for the compilers in the `alteruphono` package.
"""

# Import third-party libraries
import logging
import sys
import unittest

# Import the library being test and auxiliary libraries
import alteruphono
import tatsu

# Setup logger
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
LOGGER = logging.getLogger("TestLog")

REFERENCE = {
    "p > b": {
        "en": "the source, composed of the sound /p/, turns into the target, composed of the sound /b/",
        "pt": "a fonte, composta pelo som /p/, torna-se a meta, composta pelo som /b/",
        "fw": (" (p) ", " b "),
        "bw": (" (b) ", " p "),
    },
    "V s -> @1 z @1 / # p|b r _ t|d": {
        "en": "the source, composed of some sound of class V (vowel) followed by the sound /s/, turns into the target, composed of the first matched sound, followed by the sound /z/, followed by the first matched sound, when preceded by a word boundary, followed by either the sound /p/ or the sound /b/, followed by the sound /r/ and followed by either the sound /t/ or the sound /d/",
        "pt": "a fonte, composta por algum som da classe V (vogal) seguido pelo som /s/, torna-se a meta, composta pelo primeiro som correspondenteseguido poro som /z/seguido poro primeiro som correspondente, quando precedida por um delimitador de palavraseguido poro som /p/ ou pelo som /b/seguido poro som /r/ e quando seguida pelo som /t/ ou pelo som /d/",
        "fw": (
            " (#) (p|b) (r) (:V:) (s) (t|d) ",
            " \\1 \\2 \\3 \\4 z \\4 \\6 ",
        ),
        "bw": (
            " (#) (p|b) (r) (:V:) (z) (:V:) (t|d) ",
            " \\1 \\2 \\3 \\6 s \\7 ",
        ),
    },
    "C N -> @1 / _ #": {
        "en": "the source, composed of some sound of class C (consonant) followed by some sound of class N (nasal consonant), turns into the target, composed of the first matched sound, when followed by a word boundary",
        "pt": "a fonte, composta por algum som da classe C (consoante) seguido por algum som da classe N (consoante nasal), torna-se a meta, composta pelo primeiro som correspondente, quando seguida por um delimitador de palavra",
        "fw": (" (:C:) (:N:) (#) ", " \\1 \\3 "),
        "bw": (" (:C:) (#) ", " \\1 :N: \\2 "),
    },
    "S N S -> @1 ə @3": {
        "en": "the source, composed of some sound of class S (plosive consonant), followed by some sound of class N (nasal consonant), followed by some sound of class S (plosive consonant), turns into the target, composed of the first matched sound, followed by the sound /ə/, followed by the third matched sound",
        "pt": "a fonte, composta por algum som da classe S (consoante plosiva)seguido poralgum som da classe N (consoante nasal)seguido poralgum som da classe S (consoante plosiva), torna-se a meta, composta pelo primeiro som correspondenteseguido poro som /ə/seguido poro terceiro som correspondente",
        "fw": (" (:S:) (:N:) (:S:) ", " \\1 ə \\3 "),
        "bw": (" (:S:) (ə) (:S:) ", " \\1 :N: \\3 "),
    },
    "b -> v / V _ V|r": {
        "en": "the source, composed of the sound /b/, turns into the target, composed of the sound /v/, when preceded by some sound of class V (vowel) and followed by either some sound of class V (vowel) or the sound /r/",
        "pt": "a fonte, composta pelo som /b/, torna-se a meta, composta pelo som /v/, quando precedida por algum som da classe V (vogal) e quando seguida por algum som da classe V (vogal) ou pelo som /r/",
        "fw": (" (:V:) (b) (:V:|r) ", " \\1 v \\3 "),
        "bw": (" (:V:) (v) (:V:|r) ", " \\1 b \\3 "),
    },
    "d -> :null: / V[+long] _ #": {
        "en": "the source, composed of the sound /d/, is deleted, when preceded by some sound of class V (vowel) and followed by a word boundary",
        "pt": "a fonte, composta pelo som /d/, é apagada, quando precedida por algum som da classe V (vogal) e quando seguida por um delimitador de palavra",
        "fw": (" (:V:) (d) (#) ", " \\1 \\3 "),
        "bw": (" (:V:) (#) ", " \\1 d \\2 "),
    },
    "d|ɣ -> @1[+voiceless] / _ #": {
        "en": "the source, composed of either the sound /d/ or the sound /ɣ/, turns into the target, composed of the first matched sound (changed into a voiceless sound), when followed by a word boundary",
        "pt": "a fonte, composta pelo som /d/ ou pelo som /ɣ/, torna-se a meta, composta pelo primeiro som correspondente (mudado para um som voiceless), quando seguida por um delimitador de palavra",
        "fw": (" (d|ɣ) (#) ", " \\1 \\2 "),
        "bw": (" (d|ɣ) (#) ", " \\1 \\2 "),
    },
}


DOT_REFERENCE = 'digraph G {\ngraph [layout="dot",ordering="out",splines="polyline"] ;\n\tC0 [label="#"] ;\n\tC1 [label="_pos_"] ;\n\tS0 [label="(ipa:p)"] ;\n\tT0 [label="(ipa:b)"] ;\n\tsource [label="source"] ;\n\ttarget [label="target"] ;\n\t"context" -> "C0" ;\n\t"context" -> "C1" ;\n\t"source" -> "S0" ;\n\t"start" -> "context" ;\n\t"start" -> "source" ;\n\t"start" -> "target" ;\n\t"target" -> "T0" ;\n{rank=same;C0;C1;S0;T0} ;\n{rank=same;} ;\n}'


class TestCompilers(unittest.TestCase):
    """
    Class for `alteruphono` tests related to compilers.
    """

    def test_english(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # Load sound changes and build the compiler
        SOUND_CLASSES = alteruphono.utils.read_sound_classes()
        english = alteruphono.NLAutomata(SOUND_CLASSES, lang="en")

        for rule, ref in REFERENCE.items():
            ast = parser.parse(rule)
            en = english.compile(ast)
            assert en == ref["en"]

    def test_portuguese(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # Load sound changes and build the compiler
        SOUND_CLASSES = alteruphono.utils.read_sound_classes()
        portuguese = alteruphono.NLAutomata(SOUND_CLASSES, lang="pt")

        for rule, ref in REFERENCE.items():
            ast = parser.parse(rule)
            pt = portuguese.compile(ast)
            assert pt == ref["pt"]

    def test_forward(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # Load sound changes and build the compiler
        SOUND_CLASSES = alteruphono.utils.read_sound_classes()
        forward = alteruphono.ForwardAutomata(SOUND_CLASSES)

        for rule, ref in REFERENCE.items():
            ast = parser.parse(rule)
            fw = forward.compile(ast)
            assert fw == ref["fw"]

    def test_backward(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # Load sound changes and build the compiler
        SOUND_CLASSES = alteruphono.utils.read_sound_classes()
        backward = alteruphono.BackwardAutomata(SOUND_CLASSES)

        for rule, ref in REFERENCE.items():
            ast = parser.parse(rule)
            bw = backward.compile(ast)
            assert bw == ref["bw"]

    def test_graph(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # build the compiler
        graph = alteruphono.GraphAutomata()

        # check dot source
        graph.compile(parser.parse("p > b / # _"))
        dot = graph.dot_source()

        assert dot == DOT_REFERENCE


if __name__ == "__main__":
    unittest.main()
