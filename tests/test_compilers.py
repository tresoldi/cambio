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
    },
    "V s -> @1 z @1 / # p|b r _ t|d": {
        "en": "the source, composed of some sound of class V (vowel) followed by the sound /s/, turns into the target, composed of the first matched sound, followed by the sound /z/, followed by the first matched sound, when preceded by a word boundary, followed by either the sound /p/ or the sound /b/, followed by the sound /r/ and followed by either the sound /t/ or the sound /d/",
        "pt": "a fonte, composta por algum som da classe V (vogal) seguido pelo som /s/, torna-se a meta, composta pelo primeiro som correspondenteseguido poro som /z/seguido poro primeiro som correspondente, quando precedida por um delimitador de palavraseguido poro som /p/ ou pelo som /b/seguido poro som /r/ e quando seguida pelo som /t/ ou pelo som /d/",
    },
    "C N -> @1 / _ #": {
        "en": "the source, composed of some sound of class C (consonant) followed by some sound of class N (nasal consonant), turns into the target, composed of the first matched sound, when followed by a word boundary",
        "pt": "a fonte, composta por algum som da classe C (consoante) seguido por algum som da classe N (consoante nasal), torna-se a meta, composta pelo primeiro som correspondente, quando seguida por um delimitador de palavra",
    },
    "S N S -> @1 ə @3": {
        "en": "the source, composed of some sound of class S (plosive consonant), followed by some sound of class N (nasal consonant), followed by some sound of class S (plosive consonant), turns into the target, composed of the first matched sound, followed by the sound /ə/, followed by the third matched sound",
        "pt": "a fonte, composta por algum som da classe S (consoante plosiva)seguido poralgum som da classe N (consoante nasal)seguido poralgum som da classe S (consoante plosiva), torna-se a meta, composta pelo primeiro som correspondenteseguido poro som /ə/seguido poro terceiro som correspondente",
    },
    "b -> v / V _ V|r": {
        "en": "the source, composed of the sound /b/, turns into the target, composed of the sound /v/, when preceded by some sound of class V (vowel) and followed by either some sound of class V (vowel) or the sound /r/",
        "pt": "a fonte, composta pelo som /b/, torna-se a meta, composta pelo som /v/, quando precedida por algum som da classe V (vogal) e quando seguida por algum som da classe V (vogal) ou pelo som /r/",
    },
    "d -> :null: / V[+long] _ #": {
        "en": "the source, composed of the sound /d/, is deleted, when preceded by some sound of class V (vowel) and followed by a word boundary",
        "pt": "a fonte, composta pelo som /d/, é apagada, quando precedida por algum som da classe V (vogal) e quando seguida por um delimitador de palavra",
    },
    "d|ɣ -> @1[+voiceless] / _ #": {
        "en": "the source, composed of either the sound /d/ or the sound /ɣ/, turns into the target, composed of the first matched sound (changed into a voiceless sound), when followed by a word boundary",
        "pt": "a fonte, composta pelo som /d/ ou pelo som /ɣ/, torna-se a meta, composta pelo primeiro som correspondente (mudado para um som voiceless), quando seguida por um delimitador de palavra",
    },
}


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
            print(rule, pt)
            assert pt == ref["pt"]


if __name__ == "__main__":
    sys.exit(unittest.main())
