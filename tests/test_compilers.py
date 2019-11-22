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
            " (#) (p|b) (r) (ẽ̞ẽ̞|õ̞õ̞|ø̞̃ø̞̃|ɔ̞̈ɔ̞̈|ɞ̞̃ɞ̞̃|ɤ̞̃ɤ̞̃|ɪ̈̃ɪ̈̃|ɯ̽̃ɯ̽̃|ɵ̞̃ɵ̞̃|ʊ̈̃ʊ̈̃|ãã|a̰ːː|ẽẽ|e̞e̞|ẽ̞ː|ĩĩ|ḭːː|õõ|o̞o̞|õ̞ː|ũũ|ỹỹ|æ̃æ̃|ø̃ø̃|ø̞ø̞|ø̞̃ː|œ̃œ̃|ɐ̃ɐ̃|ɐ̹ɐ̹|ɑ̃ɑ̃|ɒ̃ɒ̃|ɔ̃ɔ̃|ɔ̞̈ː|ɘ̃ɘ̃|ə̃ə̃|ɛ̃ɛ̃|ɜ̃ɜ̃|ɞ̃ɞ̃|ɞ̞ɞ̞|ɞ̞̃ː|ɤ̃ɤ̃|ɤ̞ɤ̞|ɤ̞̃ː|ɨ̃ɨ̃|ɪ̃ɪ̃|ɪ̈ɪ̈|ɪ̈̃ː|ɯ̃ɯ̃|ɯ̽ɯ̽|ɯ̽̃ː|ɵ̃ɵ̃|ɵ̞ɵ̞|ɵ̞̃ː|ɶ̃ɶ̃|ʉ̃ʉ̃|ʊ̃ʊ̃|ʊ̈ʊ̈|ʊ̈̃ː|ʌ̃ʌ̃|ʏ̃ʏ̃|ãː|eːː|ẽː|e̞ː|e̞ˑ|ẽ̞|e̹ː|iːː|ĩː|ḭː|oːː|õː|o̞ː|õ̞|uːː|ũː|yːː|ỹː|æːː|æ̃ː|øːː|ø̃ː|ø̞ː|ø̞̃|œ̃ː|ɐ̃ː|ɐ̹ː|ɑ̃ː|ɒ̃ː|ɔ̃ː|ɔ̞̈|ɘ̃ː|ə̃ː|ɛːː|ɛ̃ː|ɛ̹̃|ɜ̃ː|ɞ̃ː|ɞ̞ː|ɞ̞̃|ɤ̃ː|ɤ̞ː|ɤ̞̃|ɨ̃ː|ɪ̃ː|ɪ̈ː|ɪ̈̃|ɯ̃ː|ɯ̥̃|ɯ̽ː|ɯ̽̃|ɵ̃ː|ɵ̞ː|ɵ̞̃|ɶ̃ː|ʉ̃ː|ʊ̃ː|ʊ̈ː|ʊ̈̃|ʌ̃ː|ʌ̤̃|ʌ̯ː|ʏ̃ː|aa|aː|aˑ|a˞|ã|ă|ḁ|a̯|a̰|ee|eː|eˑ|ẽ|ĕ|e̞|e̤|e̥|e̯|ḛ|e̹|ii|iː|iˑ|ĩ|i̤|i̥|ḭ|i̹|oo|oː|oˑ|oˤ|õ|ŏ|o̞|o̤|o̥|o̯|o̰|uu|uː|uˑ|ũ|ṳ|u̥|ṵ|yy|yː|yˑ|ỹ|ææ|æː|æˑ|æ̃|æ̰|øø|øː|øˑ|ø̃|ø̞|œœ|œː|œ̃|ɐɐ|ɐː|ɐ̃|ɐ̯|ɐ̹|ɑɑ|ɑː|ɑ̃|ɑ̟|ɒɒ|ɒː|ɒ̃|ɔɔ|ɔː|ɔ̃|ɔ̑|ɔ̯|ɔ̰|ɘɘ|ɘː|ɘ̃|əə|əː|ə˞|ə̃|ə̆|ə̰|ɛɛ|ɛː|ɛ̃|ɛ̑|ɛ̯|ɛ̰|ɜɜ|ɜː|ɜ̃|ɞɞ|ɞː|ɞ̃|ɞ̞|ɤɤ|ɤː|ɤ̃|ɤ̆|ɤ̑|ɤ̞|ɤ̯|ɨɨ|ɨː|ɨ̃|ɪɪ|ɪː|ɪ̃|ɪ̈|ɪ̥|ɪ̯|ɪ̰|ɪ̹|ɯɯ|ɯː|ɯ̃|ɯ̤|ɯ̥|ɯ̯|ɯ̽|ɵɵ|ɵː|ɵ̃|ɵ̞|ɶɶ|ɶː|ɶ̃|ʉʉ|ʉː|ʉ̃|ʉ̰|ʊʊ|ʊː|ʊ̃|ʊ̈|ʊ̥|ʊ̯|ʊ̰|ʌʌ|ʌː|ʌ̃|ʌ̆|ʌ̤|ʏʏ|ʏː|ʏ̃|a|e|i|o|u|y|æ|ø|œ|ɐ|ɑ|ɒ|ɔ|ɘ|ə|ɛ|ɜ|ɞ|ɤ|ɨ|ɪ|ɯ|ɵ|ɶ|ɿ|ʅ|ʉ|ʊ|ʌ|ʏ|ʮ|ʯ|ᴀ) (s) (t|d) ",
            " \\1 \\2 \\3 \\4 z \\4 \\6 ",
        ),
        "bw": (" (#) (p|b) (r) (V) (z) (V) (t|d) ", " \\1 \\2 \\3 \\6 s \\7 "),
    },
    "C N -> @1 / _ #": {
        "en": "the source, composed of some sound of class C (consonant) followed by some sound of class N (nasal consonant), turns into the target, composed of the first matched sound, when followed by a word boundary",
        "pt": "a fonte, composta por algum som da classe C (consoante) seguido por algum som da classe N (consoante nasal), torna-se a meta, composta pelo primeiro som correspondente, quando seguida por um delimitador de palavra",
        "fw": (
            " (d̪z̪ː|d̪ːz̪|t̠ʃʼː|t̪s̪ʰ|t̪s̪ʲ|t̪s̪ʼ|t̪s̪ː|t̪ɬ̪ʰ|t̪ɬ̪ʼ|t̪ːs̪|cçʰ|dz̪ː|d̠ʒʷ|d̠ʒː|d̠ʒ̤|d̪z̪|d̪ʱː|d̪ːʱ|d̪̥̚|d̪̥ⁿ|ts̪ʰ|ts̪ʲ|ts̪ʼ|ts̪ː|tɬ̪ʰ|tɬ̪ʼ|tʃʼː|tːs̪|tːʃʼ|t̠ʃʰ|t̠ʃʷ|t̠ʃʼ|t̠ʃː|t̪s̪|t̪ɬ̪|t̪ʰʲ|t̪ʰː|t̪ʷʰ|t̪ːʰ|ŋgǀǀ|ŋgǃǃ|ŋ̊ǀǀ|ŋ̊ǃǃ|ʰt̪ʰ|ˀŋǀǀ|ˀŋǃǃ|ⁿgǀǀ|ⁿgǃǃ|bʰː|bʱː|bʷː|bːʰ|bːʱ|bːʷ|bːˤ|bˤː|b̥ʰ|cç|dzː|dz̪|dʑː|dʒʱ|dʒʲ|dʒʷ|dʰː|dʱː|dːz|dːʑ|dːʒ|dːʰ|dːʱ|d̠ʒ|d̤ʒ|d̤ː|d̥̚|d̥ⁿ|d̪ð|d̪ɮ|d̪ʱ|d̪ʲ|d̪ː|d̪ˠ|d̪ˤ|d̪̈|d̪̚|d̪̤|d̪̰|d̪ⁿ|fʷː|fːʷ|gǃǃ|g̊ʰ|kwh|kǃǃ|kʷʰ|kʷʼ|kʷː|kʼʷ|k\uf268ʼ|l̠ʲ|l̪ʲ|l̪ː|l̪̍|l̪̥|l̪̩|mʷː|mːʷ|mːˤ|mˤː|n̪ˠ|oz̻|pfʰ|pfʼ|pʰʲ|pʰː|pːʰ|qʰʷ|qʷʰ|qʷʼ|qʼʷ|qʼ↓|rːˤ|rˤː|r̪ː|r̪ˤ|r̪̥|s̪ʲ|s̪ʼ|s̪ˠ|tsʰ|tsʲ|tsʼ|tsː|ts̪|tɕʰ|tɕː|tɬʰ|tɬʼ|tɬ̪|tʂʰ|tʂː|tʃʰ|tʃʲ|tʃʷ|tʃʼ|tʃː|tʰʷ|tʲʰ|tʷʰ|tːs|tːɕ|tːʂ|tːʃ|t̠ʃ|t̪ʰ|t̪ʲ|t̪ʷ|t̪ʼ|t̪ː|t̪ˠ|t̪ˤ|t̪̚|t̪θ|t̪ⁿ|z̪̥|ŋgǀ|ŋgǁ|ŋgǂ|ŋgǃ|ŋgʘ|ŋǀǀ|ŋǃǃ|ŋ̊ǀ|ŋ̊ǁ|ŋ̊ǂ|ŋ̊ǃ|ŋ̊ʘ|ɖːʐ|ɬ̪ʼ|ʈʂʰ|ʈʂː|ʈʂ’|ʈʰː|ʈːʂ|ʈːʰ|ʰtʰ|ʰt̪|ˀŋǀ|ˀŋǁ|ˀŋǂ|ˀŋǃ|ˀŋʘ|ⁿdʒ|ⁿd̪|ⁿd̼|ⁿgǀ|ⁿgǁ|ⁿgǂ|ⁿgǃ|ⁿgʘ|ⁿkʷ|ⁿtʃ|ⁿt̪|bv|bʰ|bʱ|bʲ|bʷ|bː|bˠ|b̚|b̡|b̤|b̥|b̪|bβ|bᵛ|bᵝ|bⁿ|cʰ|cʼ|cː|ç|dz|dð|dɮ|dʐ|dʑ|dʒ|dʰ|dʱ|dʲ|dː|dˤ|d̂|d̠|d̤|d̥|d̪|d̰|d̼|dᶞ|dᶻ|dᶼ|dᶽ|dⁿ|fʰ|fʲ|fʼ|fˈ|fː|fˠ|gǀ|gǁ|gǂ|gǃ|gɣ|gʘ|gʰ|gʱ|gʲ|gʷ|gː|gˠ|g̈|g̊|g̥|h̃|h̬|jː|j̃|j̊|j̥|kh|kw|kx|kǀ|kǁ|kǂ|kǃ|kʘ|kʰ|kʲ|kʷ|kʼ|kː|kˣ|k̚|k̬|k\uf268|lʱ|lʲ|lː|lˠ|l̂|l̠|ḷ|l̤|l̥|l̩|l̪|l̻|l̼|mʰ|mʱ|mʲ|mʷ|mː|mˠ|ṃ|m̤|m̥|m̩|nʲ|nː|nˤ|n̂|ñ|n̊|ṇ|n̥|n̩|n̪|n̰|n̻|n̼|pf|ph|pɸ|pʰ|pʲ|pʷ|pʼ|pː|pˠ|p̚|p̪|p̬|pᶠ|pᶲ|qʰ|qʷ|qʼ|q̚|qχ|qᵡ|rʲ|rː|rˤ|r̃|r̥|r̩|r̪|r̼|sʲ|sʼ|sː|sˠ|s̩|s̪|s̬|s̻|th|ts|tɕ|tɬ|tʂ|tʃ|tʰ|tʲ|tʷ|tʼ|tː|tˢ|tˤ|t̂|t̚|t̠|t̪|t̬|t̼|tθ|tᶝ|tᶳ|tᶴ|tᶿ|tⁿ|vʲ|vː|v̆|v̥|v̩|wː|wˠ|w̃|xʲ|xʷ|xʼ|ẋ|zʲ|z̥|z̩|z̪|ðː|ð̚|ð̞|ð̼|ð͉|ŋǀ|ŋǁ|ŋǂ|ŋǃ|ŋʘ|ŋʷ|ŋː|ŋ̊|ŋ̍|ŋ̥|ŋ̩|ǃǃ|ȵ̊|ɓʲ|ɖʐ|ɖʱ|ɖ̤|ɖᶼ|ɗ̥|ɟʝ|ɡ̤|ɢʁ|ɢʰ|ɢʶ|ɣʷ|ɣ̊|ɣ̥|ɬʼ|ɬ̪|ɬ̼|ɭ̊|ɭ̍|ɭ̩|ɮ̼|ɱ̊|ɱ̥|ɲː|ɲ̊|ɲ̍|ɲ̥|ɳ̊|ɳ̍|ɴ̥|ɴ̩|ɹ̠|ɹ̩|ɽʱ|ɽ̈|ɾ̥|ɾ̼|ʀ̥|ʁ̞|ʁ̥|ʃʲ|ʃʼ|ʇ̼|ʈʂ|ʈʰ|ʈ̬|ʈᶳ|ʎ̟|ʎ̥|ʒ̊|ʒ̍|ʒ̩|ʔh|ʔʲ|ʔʷ|ʙ̥|ʙ̩|ʛ̥|ʟ̥|ʦː|ʰk|ʰp|ʰt|βʷ|β̞|θː|θ̬|θ̼|χʷ|χʼ|ⁿb|ⁿd|ⁿg|ⁿk|ⁿp|ⁿt|ⁿɟ|b|c|d|f|g|h|j|k|l|m|n|p|q|r|s|t|v|w|x|z|ð|ħ|ŋ|ƛ|ƫ|ǀ|ǁ|ǂ|ǃ|ȡ|ȴ|ȵ|ȶ|ɓ|ɕ|ɖ|ɗ|ɟ|ɠ|ɢ|ɣ|ɥ|ɦ|ɧ|ɫ|ɬ|ɭ|ɮ|ɰ|ɱ|ɲ|ɳ|ɴ|ɸ|ɹ|ɺ|ɻ|ɽ|ɾ|ʀ|ʁ|ʂ|ʃ|ʄ|ʆ|ʈ|ʋ|ʍ|ʎ|ʐ|ʑ|ʒ|ʔ|ʕ|ʘ|ʙ|ʛ|ʜ|ʝ|ʟ|ʠ|ʡ|ʢ|ʣ|ʤ|ʥ|ʦ|ʧ|ʨ|β|θ|χ|ᶀ|ᶁ|ᶂ|ᶃ|ᶄ|ᶅ|ᶆ|ᶇ|ᶈ|ᶉ|ᶊ|ᶋ|ᶌ|ᶍ|ᶎ|ᶑ|ⱱ) (mʷː|mːʷ|mːˤ|mˤː|n̪ˠ|mʰ|mʱ|mʲ|mʷ|mː|mˠ|ṃ|m̤|m̥|m̩|nʲ|nː|nˤ|n̂|ñ|n̊|ṇ|n̥|n̩|n̪|n̰|n̻|n̼|ŋʷ|ŋː|ŋ̊|ŋ̍|ŋ̥|ŋ̩|ȵ̊|ɱ̊|ɱ̥|ɲː|ɲ̊|ɲ̍|ɲ̥|ɳ̊|ɳ̍|ɴ̥|ɴ̩|m|n|ŋ|ȵ|ɱ|ɲ|ɳ|ɴ|ᶆ|ᶇ) (#) ",
            " \\1 \\3 ",
        ),
        "bw": (" (C) (#) ", " \\1 N \\2 "),
    },
    "S N S -> @1 ə @3": {
        "en": "the source, composed of some sound of class S (plosive consonant), followed by some sound of class N (nasal consonant), followed by some sound of class S (plosive consonant), turns into the target, composed of the first matched sound, followed by the sound /ə/, followed by the third matched sound",
        "pt": "a fonte, composta por algum som da classe S (consoante plosiva)seguido poralgum som da classe N (consoante nasal)seguido poralgum som da classe S (consoante plosiva), torna-se a meta, composta pelo primeiro som correspondenteseguido poro som /ə/seguido poro terceiro som correspondente",
        "fw": (
            " (d̪ʱː|d̪ːʱ|d̪̥̚|d̪̥ⁿ|t̪ʰʲ|t̪ʰː|t̪ʷʰ|t̪ːʰ|ʰt̪ʰ|bʰː|bʱː|bʷː|bːʰ|bːʱ|bːʷ|bːˤ|bˤː|b̥ʰ|dʰː|dʱː|dːʰ|dːʱ|d̤ː|d̥̚|d̥ⁿ|d̪ʱ|d̪ʲ|d̪ː|d̪ˠ|d̪ˤ|d̪̈|d̪̚|d̪̤|d̪̰|d̪ⁿ|g̊ʰ|kwh|kʷʰ|kʷʼ|kʷː|kʼʷ|pʰʲ|pʰː|pːʰ|qʰʷ|qʷʰ|qʷʼ|qʼʷ|tʰʷ|tʲʰ|tʷʰ|t̪ʰ|t̪ʲ|t̪ʷ|t̪ʼ|t̪ː|t̪ˠ|t̪ˤ|t̪̚|t̪ⁿ|ʈʰː|ʈːʰ|ʰtʰ|ʰt̪|ⁿd̪|ⁿd̼|ⁿkʷ|ⁿt̪|bʰ|bʱ|bʲ|bʷ|bː|bˠ|b̚|b̡|b̤|b̥|b̪|bⁿ|cʰ|cʼ|cː|dʰ|dʱ|dʲ|dː|dˤ|d̂|d̠|d̤|d̥|d̪|d̰|d̼|dⁿ|gʰ|gʱ|gʲ|gʷ|gː|g̈|g̊|g̥|kh|kw|kʰ|kʲ|kʷ|kʼ|kː|k̚|k̬|ph|pʰ|pʲ|pʷ|pʼ|pː|pˠ|p̚|p̪|p̬|qʰ|qʷ|qʼ|q̚|th|tʰ|tʲ|tʷ|tʼ|tː|tˤ|t̂|t̚|t̠|t̪|t̬|t̼|tⁿ|ɖʱ|ɖ̤|ɡ̤|ɢʰ|ʈʰ|ʈ̬|ʔʲ|ʔʷ|ʰk|ʰp|ʰt|ⁿb|ⁿd|ⁿg|ⁿk|ⁿp|ⁿt|ⁿɟ|b|c|d|g|k|p|q|t|ƫ|ȡ|ȶ|ɖ|ɟ|ɢ|ʈ|ʔ|ʡ|ᶀ|ᶁ|ᶃ|ᶄ|ᶈ) (mʷː|mːʷ|mːˤ|mˤː|n̪ˠ|mʰ|mʱ|mʲ|mʷ|mː|mˠ|ṃ|m̤|m̥|m̩|nʲ|nː|nˤ|n̂|ñ|n̊|ṇ|n̥|n̩|n̪|n̰|n̻|n̼|ŋʷ|ŋː|ŋ̊|ŋ̍|ŋ̥|ŋ̩|ȵ̊|ɱ̊|ɱ̥|ɲː|ɲ̊|ɲ̍|ɲ̥|ɳ̊|ɳ̍|ɴ̥|ɴ̩|m|n|ŋ|ȵ|ɱ|ɲ|ɳ|ɴ|ᶆ|ᶇ) (d̪ʱː|d̪ːʱ|d̪̥̚|d̪̥ⁿ|t̪ʰʲ|t̪ʰː|t̪ʷʰ|t̪ːʰ|ʰt̪ʰ|bʰː|bʱː|bʷː|bːʰ|bːʱ|bːʷ|bːˤ|bˤː|b̥ʰ|dʰː|dʱː|dːʰ|dːʱ|d̤ː|d̥̚|d̥ⁿ|d̪ʱ|d̪ʲ|d̪ː|d̪ˠ|d̪ˤ|d̪̈|d̪̚|d̪̤|d̪̰|d̪ⁿ|g̊ʰ|kwh|kʷʰ|kʷʼ|kʷː|kʼʷ|pʰʲ|pʰː|pːʰ|qʰʷ|qʷʰ|qʷʼ|qʼʷ|tʰʷ|tʲʰ|tʷʰ|t̪ʰ|t̪ʲ|t̪ʷ|t̪ʼ|t̪ː|t̪ˠ|t̪ˤ|t̪̚|t̪ⁿ|ʈʰː|ʈːʰ|ʰtʰ|ʰt̪|ⁿd̪|ⁿd̼|ⁿkʷ|ⁿt̪|bʰ|bʱ|bʲ|bʷ|bː|bˠ|b̚|b̡|b̤|b̥|b̪|bⁿ|cʰ|cʼ|cː|dʰ|dʱ|dʲ|dː|dˤ|d̂|d̠|d̤|d̥|d̪|d̰|d̼|dⁿ|gʰ|gʱ|gʲ|gʷ|gː|g̈|g̊|g̥|kh|kw|kʰ|kʲ|kʷ|kʼ|kː|k̚|k̬|ph|pʰ|pʲ|pʷ|pʼ|pː|pˠ|p̚|p̪|p̬|qʰ|qʷ|qʼ|q̚|th|tʰ|tʲ|tʷ|tʼ|tː|tˤ|t̂|t̚|t̠|t̪|t̬|t̼|tⁿ|ɖʱ|ɖ̤|ɡ̤|ɢʰ|ʈʰ|ʈ̬|ʔʲ|ʔʷ|ʰk|ʰp|ʰt|ⁿb|ⁿd|ⁿg|ⁿk|ⁿp|ⁿt|ⁿɟ|b|c|d|g|k|p|q|t|ƫ|ȡ|ȶ|ɖ|ɟ|ɢ|ʈ|ʔ|ʡ|ᶀ|ᶁ|ᶃ|ᶄ|ᶈ) ",
            " \\1 ə \\3 ",
        ),
        "bw": (" (S) (ə) (S) ", " \\1 N \\3 "),
    },
    "b -> v / V _ V|r": {
        "en": "the source, composed of the sound /b/, turns into the target, composed of the sound /v/, when preceded by some sound of class V (vowel) and followed by either some sound of class V (vowel) or the sound /r/",
        "pt": "a fonte, composta pelo som /b/, torna-se a meta, composta pelo som /v/, quando precedida por algum som da classe V (vogal) e quando seguida por algum som da classe V (vogal) ou pelo som /r/",
        "fw": (
            " (ẽ̞ẽ̞|õ̞õ̞|ø̞̃ø̞̃|ɔ̞̈ɔ̞̈|ɞ̞̃ɞ̞̃|ɤ̞̃ɤ̞̃|ɪ̈̃ɪ̈̃|ɯ̽̃ɯ̽̃|ɵ̞̃ɵ̞̃|ʊ̈̃ʊ̈̃|ãã|a̰ːː|ẽẽ|e̞e̞|ẽ̞ː|ĩĩ|ḭːː|õõ|o̞o̞|õ̞ː|ũũ|ỹỹ|æ̃æ̃|ø̃ø̃|ø̞ø̞|ø̞̃ː|œ̃œ̃|ɐ̃ɐ̃|ɐ̹ɐ̹|ɑ̃ɑ̃|ɒ̃ɒ̃|ɔ̃ɔ̃|ɔ̞̈ː|ɘ̃ɘ̃|ə̃ə̃|ɛ̃ɛ̃|ɜ̃ɜ̃|ɞ̃ɞ̃|ɞ̞ɞ̞|ɞ̞̃ː|ɤ̃ɤ̃|ɤ̞ɤ̞|ɤ̞̃ː|ɨ̃ɨ̃|ɪ̃ɪ̃|ɪ̈ɪ̈|ɪ̈̃ː|ɯ̃ɯ̃|ɯ̽ɯ̽|ɯ̽̃ː|ɵ̃ɵ̃|ɵ̞ɵ̞|ɵ̞̃ː|ɶ̃ɶ̃|ʉ̃ʉ̃|ʊ̃ʊ̃|ʊ̈ʊ̈|ʊ̈̃ː|ʌ̃ʌ̃|ʏ̃ʏ̃|ãː|eːː|ẽː|e̞ː|e̞ˑ|ẽ̞|e̹ː|iːː|ĩː|ḭː|oːː|õː|o̞ː|õ̞|uːː|ũː|yːː|ỹː|æːː|æ̃ː|øːː|ø̃ː|ø̞ː|ø̞̃|œ̃ː|ɐ̃ː|ɐ̹ː|ɑ̃ː|ɒ̃ː|ɔ̃ː|ɔ̞̈|ɘ̃ː|ə̃ː|ɛːː|ɛ̃ː|ɛ̹̃|ɜ̃ː|ɞ̃ː|ɞ̞ː|ɞ̞̃|ɤ̃ː|ɤ̞ː|ɤ̞̃|ɨ̃ː|ɪ̃ː|ɪ̈ː|ɪ̈̃|ɯ̃ː|ɯ̥̃|ɯ̽ː|ɯ̽̃|ɵ̃ː|ɵ̞ː|ɵ̞̃|ɶ̃ː|ʉ̃ː|ʊ̃ː|ʊ̈ː|ʊ̈̃|ʌ̃ː|ʌ̤̃|ʌ̯ː|ʏ̃ː|aa|aː|aˑ|a˞|ã|ă|ḁ|a̯|a̰|ee|eː|eˑ|ẽ|ĕ|e̞|e̤|e̥|e̯|ḛ|e̹|ii|iː|iˑ|ĩ|i̤|i̥|ḭ|i̹|oo|oː|oˑ|oˤ|õ|ŏ|o̞|o̤|o̥|o̯|o̰|uu|uː|uˑ|ũ|ṳ|u̥|ṵ|yy|yː|yˑ|ỹ|ææ|æː|æˑ|æ̃|æ̰|øø|øː|øˑ|ø̃|ø̞|œœ|œː|œ̃|ɐɐ|ɐː|ɐ̃|ɐ̯|ɐ̹|ɑɑ|ɑː|ɑ̃|ɑ̟|ɒɒ|ɒː|ɒ̃|ɔɔ|ɔː|ɔ̃|ɔ̑|ɔ̯|ɔ̰|ɘɘ|ɘː|ɘ̃|əə|əː|ə˞|ə̃|ə̆|ə̰|ɛɛ|ɛː|ɛ̃|ɛ̑|ɛ̯|ɛ̰|ɜɜ|ɜː|ɜ̃|ɞɞ|ɞː|ɞ̃|ɞ̞|ɤɤ|ɤː|ɤ̃|ɤ̆|ɤ̑|ɤ̞|ɤ̯|ɨɨ|ɨː|ɨ̃|ɪɪ|ɪː|ɪ̃|ɪ̈|ɪ̥|ɪ̯|ɪ̰|ɪ̹|ɯɯ|ɯː|ɯ̃|ɯ̤|ɯ̥|ɯ̯|ɯ̽|ɵɵ|ɵː|ɵ̃|ɵ̞|ɶɶ|ɶː|ɶ̃|ʉʉ|ʉː|ʉ̃|ʉ̰|ʊʊ|ʊː|ʊ̃|ʊ̈|ʊ̥|ʊ̯|ʊ̰|ʌʌ|ʌː|ʌ̃|ʌ̆|ʌ̤|ʏʏ|ʏː|ʏ̃|a|e|i|o|u|y|æ|ø|œ|ɐ|ɑ|ɒ|ɔ|ɘ|ə|ɛ|ɜ|ɞ|ɤ|ɨ|ɪ|ɯ|ɵ|ɶ|ɿ|ʅ|ʉ|ʊ|ʌ|ʏ|ʮ|ʯ|ᴀ) (b) (ẽ̞ẽ̞|õ̞õ̞|ø̞̃ø̞̃|ɔ̞̈ɔ̞̈|ɞ̞̃ɞ̞̃|ɤ̞̃ɤ̞̃|ɪ̈̃ɪ̈̃|ɯ̽̃ɯ̽̃|ɵ̞̃ɵ̞̃|ʊ̈̃ʊ̈̃|ãã|a̰ːː|ẽẽ|e̞e̞|ẽ̞ː|ĩĩ|ḭːː|õõ|o̞o̞|õ̞ː|ũũ|ỹỹ|æ̃æ̃|ø̃ø̃|ø̞ø̞|ø̞̃ː|œ̃œ̃|ɐ̃ɐ̃|ɐ̹ɐ̹|ɑ̃ɑ̃|ɒ̃ɒ̃|ɔ̃ɔ̃|ɔ̞̈ː|ɘ̃ɘ̃|ə̃ə̃|ɛ̃ɛ̃|ɜ̃ɜ̃|ɞ̃ɞ̃|ɞ̞ɞ̞|ɞ̞̃ː|ɤ̃ɤ̃|ɤ̞ɤ̞|ɤ̞̃ː|ɨ̃ɨ̃|ɪ̃ɪ̃|ɪ̈ɪ̈|ɪ̈̃ː|ɯ̃ɯ̃|ɯ̽ɯ̽|ɯ̽̃ː|ɵ̃ɵ̃|ɵ̞ɵ̞|ɵ̞̃ː|ɶ̃ɶ̃|ʉ̃ʉ̃|ʊ̃ʊ̃|ʊ̈ʊ̈|ʊ̈̃ː|ʌ̃ʌ̃|ʏ̃ʏ̃|ãː|eːː|ẽː|e̞ː|e̞ˑ|ẽ̞|e̹ː|iːː|ĩː|ḭː|oːː|õː|o̞ː|õ̞|uːː|ũː|yːː|ỹː|æːː|æ̃ː|øːː|ø̃ː|ø̞ː|ø̞̃|œ̃ː|ɐ̃ː|ɐ̹ː|ɑ̃ː|ɒ̃ː|ɔ̃ː|ɔ̞̈|ɘ̃ː|ə̃ː|ɛːː|ɛ̃ː|ɛ̹̃|ɜ̃ː|ɞ̃ː|ɞ̞ː|ɞ̞̃|ɤ̃ː|ɤ̞ː|ɤ̞̃|ɨ̃ː|ɪ̃ː|ɪ̈ː|ɪ̈̃|ɯ̃ː|ɯ̥̃|ɯ̽ː|ɯ̽̃|ɵ̃ː|ɵ̞ː|ɵ̞̃|ɶ̃ː|ʉ̃ː|ʊ̃ː|ʊ̈ː|ʊ̈̃|ʌ̃ː|ʌ̤̃|ʌ̯ː|ʏ̃ː|aa|aː|aˑ|a˞|ã|ă|ḁ|a̯|a̰|ee|eː|eˑ|ẽ|ĕ|e̞|e̤|e̥|e̯|ḛ|e̹|ii|iː|iˑ|ĩ|i̤|i̥|ḭ|i̹|oo|oː|oˑ|oˤ|õ|ŏ|o̞|o̤|o̥|o̯|o̰|uu|uː|uˑ|ũ|ṳ|u̥|ṵ|yy|yː|yˑ|ỹ|ææ|æː|æˑ|æ̃|æ̰|øø|øː|øˑ|ø̃|ø̞|œœ|œː|œ̃|ɐɐ|ɐː|ɐ̃|ɐ̯|ɐ̹|ɑɑ|ɑː|ɑ̃|ɑ̟|ɒɒ|ɒː|ɒ̃|ɔɔ|ɔː|ɔ̃|ɔ̑|ɔ̯|ɔ̰|ɘɘ|ɘː|ɘ̃|əə|əː|ə˞|ə̃|ə̆|ə̰|ɛɛ|ɛː|ɛ̃|ɛ̑|ɛ̯|ɛ̰|ɜɜ|ɜː|ɜ̃|ɞɞ|ɞː|ɞ̃|ɞ̞|ɤɤ|ɤː|ɤ̃|ɤ̆|ɤ̑|ɤ̞|ɤ̯|ɨɨ|ɨː|ɨ̃|ɪɪ|ɪː|ɪ̃|ɪ̈|ɪ̥|ɪ̯|ɪ̰|ɪ̹|ɯɯ|ɯː|ɯ̃|ɯ̤|ɯ̥|ɯ̯|ɯ̽|ɵɵ|ɵː|ɵ̃|ɵ̞|ɶɶ|ɶː|ɶ̃|ʉʉ|ʉː|ʉ̃|ʉ̰|ʊʊ|ʊː|ʊ̃|ʊ̈|ʊ̥|ʊ̯|ʊ̰|ʌʌ|ʌː|ʌ̃|ʌ̆|ʌ̤|ʏʏ|ʏː|ʏ̃|a|e|i|o|u|y|æ|ø|œ|ɐ|ɑ|ɒ|ɔ|ɘ|ə|ɛ|ɜ|ɞ|ɤ|ɨ|ɪ|ɯ|ɵ|ɶ|ɿ|ʅ|ʉ|ʊ|ʌ|ʏ|ʮ|ʯ|ᴀ|r) ",
            " \\1 v \\3 ",
        ),
        "bw": (
            " (ẽ̞ẽ̞|õ̞õ̞|ø̞̃ø̞̃|ɔ̞̈ɔ̞̈|ɞ̞̃ɞ̞̃|ɤ̞̃ɤ̞̃|ɪ̈̃ɪ̈̃|ɯ̽̃ɯ̽̃|ɵ̞̃ɵ̞̃|ʊ̈̃ʊ̈̃|ãã|a̰ːː|ẽẽ|e̞e̞|ẽ̞ː|ĩĩ|ḭːː|õõ|o̞o̞|õ̞ː|ũũ|ỹỹ|æ̃æ̃|ø̃ø̃|ø̞ø̞|ø̞̃ː|œ̃œ̃|ɐ̃ɐ̃|ɐ̹ɐ̹|ɑ̃ɑ̃|ɒ̃ɒ̃|ɔ̃ɔ̃|ɔ̞̈ː|ɘ̃ɘ̃|ə̃ə̃|ɛ̃ɛ̃|ɜ̃ɜ̃|ɞ̃ɞ̃|ɞ̞ɞ̞|ɞ̞̃ː|ɤ̃ɤ̃|ɤ̞ɤ̞|ɤ̞̃ː|ɨ̃ɨ̃|ɪ̃ɪ̃|ɪ̈ɪ̈|ɪ̈̃ː|ɯ̃ɯ̃|ɯ̽ɯ̽|ɯ̽̃ː|ɵ̃ɵ̃|ɵ̞ɵ̞|ɵ̞̃ː|ɶ̃ɶ̃|ʉ̃ʉ̃|ʊ̃ʊ̃|ʊ̈ʊ̈|ʊ̈̃ː|ʌ̃ʌ̃|ʏ̃ʏ̃|ãː|eːː|ẽː|e̞ː|e̞ˑ|ẽ̞|e̹ː|iːː|ĩː|ḭː|oːː|õː|o̞ː|õ̞|uːː|ũː|yːː|ỹː|æːː|æ̃ː|øːː|ø̃ː|ø̞ː|ø̞̃|œ̃ː|ɐ̃ː|ɐ̹ː|ɑ̃ː|ɒ̃ː|ɔ̃ː|ɔ̞̈|ɘ̃ː|ə̃ː|ɛːː|ɛ̃ː|ɛ̹̃|ɜ̃ː|ɞ̃ː|ɞ̞ː|ɞ̞̃|ɤ̃ː|ɤ̞ː|ɤ̞̃|ɨ̃ː|ɪ̃ː|ɪ̈ː|ɪ̈̃|ɯ̃ː|ɯ̥̃|ɯ̽ː|ɯ̽̃|ɵ̃ː|ɵ̞ː|ɵ̞̃|ɶ̃ː|ʉ̃ː|ʊ̃ː|ʊ̈ː|ʊ̈̃|ʌ̃ː|ʌ̤̃|ʌ̯ː|ʏ̃ː|aa|aː|aˑ|a˞|ã|ă|ḁ|a̯|a̰|ee|eː|eˑ|ẽ|ĕ|e̞|e̤|e̥|e̯|ḛ|e̹|ii|iː|iˑ|ĩ|i̤|i̥|ḭ|i̹|oo|oː|oˑ|oˤ|õ|ŏ|o̞|o̤|o̥|o̯|o̰|uu|uː|uˑ|ũ|ṳ|u̥|ṵ|yy|yː|yˑ|ỹ|ææ|æː|æˑ|æ̃|æ̰|øø|øː|øˑ|ø̃|ø̞|œœ|œː|œ̃|ɐɐ|ɐː|ɐ̃|ɐ̯|ɐ̹|ɑɑ|ɑː|ɑ̃|ɑ̟|ɒɒ|ɒː|ɒ̃|ɔɔ|ɔː|ɔ̃|ɔ̑|ɔ̯|ɔ̰|ɘɘ|ɘː|ɘ̃|əə|əː|ə˞|ə̃|ə̆|ə̰|ɛɛ|ɛː|ɛ̃|ɛ̑|ɛ̯|ɛ̰|ɜɜ|ɜː|ɜ̃|ɞɞ|ɞː|ɞ̃|ɞ̞|ɤɤ|ɤː|ɤ̃|ɤ̆|ɤ̑|ɤ̞|ɤ̯|ɨɨ|ɨː|ɨ̃|ɪɪ|ɪː|ɪ̃|ɪ̈|ɪ̥|ɪ̯|ɪ̰|ɪ̹|ɯɯ|ɯː|ɯ̃|ɯ̤|ɯ̥|ɯ̯|ɯ̽|ɵɵ|ɵː|ɵ̃|ɵ̞|ɶɶ|ɶː|ɶ̃|ʉʉ|ʉː|ʉ̃|ʉ̰|ʊʊ|ʊː|ʊ̃|ʊ̈|ʊ̥|ʊ̯|ʊ̰|ʌʌ|ʌː|ʌ̃|ʌ̆|ʌ̤|ʏʏ|ʏː|ʏ̃|a|e|i|o|u|y|æ|ø|œ|ɐ|ɑ|ɒ|ɔ|ɘ|ə|ɛ|ɜ|ɞ|ɤ|ɨ|ɪ|ɯ|ɵ|ɶ|ɿ|ʅ|ʉ|ʊ|ʌ|ʏ|ʮ|ʯ|ᴀ) (v) (ẽ̞ẽ̞|õ̞õ̞|ø̞̃ø̞̃|ɔ̞̈ɔ̞̈|ɞ̞̃ɞ̞̃|ɤ̞̃ɤ̞̃|ɪ̈̃ɪ̈̃|ɯ̽̃ɯ̽̃|ɵ̞̃ɵ̞̃|ʊ̈̃ʊ̈̃|ãã|a̰ːː|ẽẽ|e̞e̞|ẽ̞ː|ĩĩ|ḭːː|õõ|o̞o̞|õ̞ː|ũũ|ỹỹ|æ̃æ̃|ø̃ø̃|ø̞ø̞|ø̞̃ː|œ̃œ̃|ɐ̃ɐ̃|ɐ̹ɐ̹|ɑ̃ɑ̃|ɒ̃ɒ̃|ɔ̃ɔ̃|ɔ̞̈ː|ɘ̃ɘ̃|ə̃ə̃|ɛ̃ɛ̃|ɜ̃ɜ̃|ɞ̃ɞ̃|ɞ̞ɞ̞|ɞ̞̃ː|ɤ̃ɤ̃|ɤ̞ɤ̞|ɤ̞̃ː|ɨ̃ɨ̃|ɪ̃ɪ̃|ɪ̈ɪ̈|ɪ̈̃ː|ɯ̃ɯ̃|ɯ̽ɯ̽|ɯ̽̃ː|ɵ̃ɵ̃|ɵ̞ɵ̞|ɵ̞̃ː|ɶ̃ɶ̃|ʉ̃ʉ̃|ʊ̃ʊ̃|ʊ̈ʊ̈|ʊ̈̃ː|ʌ̃ʌ̃|ʏ̃ʏ̃|ãː|eːː|ẽː|e̞ː|e̞ˑ|ẽ̞|e̹ː|iːː|ĩː|ḭː|oːː|õː|o̞ː|õ̞|uːː|ũː|yːː|ỹː|æːː|æ̃ː|øːː|ø̃ː|ø̞ː|ø̞̃|œ̃ː|ɐ̃ː|ɐ̹ː|ɑ̃ː|ɒ̃ː|ɔ̃ː|ɔ̞̈|ɘ̃ː|ə̃ː|ɛːː|ɛ̃ː|ɛ̹̃|ɜ̃ː|ɞ̃ː|ɞ̞ː|ɞ̞̃|ɤ̃ː|ɤ̞ː|ɤ̞̃|ɨ̃ː|ɪ̃ː|ɪ̈ː|ɪ̈̃|ɯ̃ː|ɯ̥̃|ɯ̽ː|ɯ̽̃|ɵ̃ː|ɵ̞ː|ɵ̞̃|ɶ̃ː|ʉ̃ː|ʊ̃ː|ʊ̈ː|ʊ̈̃|ʌ̃ː|ʌ̤̃|ʌ̯ː|ʏ̃ː|aa|aː|aˑ|a˞|ã|ă|ḁ|a̯|a̰|ee|eː|eˑ|ẽ|ĕ|e̞|e̤|e̥|e̯|ḛ|e̹|ii|iː|iˑ|ĩ|i̤|i̥|ḭ|i̹|oo|oː|oˑ|oˤ|õ|ŏ|o̞|o̤|o̥|o̯|o̰|uu|uː|uˑ|ũ|ṳ|u̥|ṵ|yy|yː|yˑ|ỹ|ææ|æː|æˑ|æ̃|æ̰|øø|øː|øˑ|ø̃|ø̞|œœ|œː|œ̃|ɐɐ|ɐː|ɐ̃|ɐ̯|ɐ̹|ɑɑ|ɑː|ɑ̃|ɑ̟|ɒɒ|ɒː|ɒ̃|ɔɔ|ɔː|ɔ̃|ɔ̑|ɔ̯|ɔ̰|ɘɘ|ɘː|ɘ̃|əə|əː|ə˞|ə̃|ə̆|ə̰|ɛɛ|ɛː|ɛ̃|ɛ̑|ɛ̯|ɛ̰|ɜɜ|ɜː|ɜ̃|ɞɞ|ɞː|ɞ̃|ɞ̞|ɤɤ|ɤː|ɤ̃|ɤ̆|ɤ̑|ɤ̞|ɤ̯|ɨɨ|ɨː|ɨ̃|ɪɪ|ɪː|ɪ̃|ɪ̈|ɪ̥|ɪ̯|ɪ̰|ɪ̹|ɯɯ|ɯː|ɯ̃|ɯ̤|ɯ̥|ɯ̯|ɯ̽|ɵɵ|ɵː|ɵ̃|ɵ̞|ɶɶ|ɶː|ɶ̃|ʉʉ|ʉː|ʉ̃|ʉ̰|ʊʊ|ʊː|ʊ̃|ʊ̈|ʊ̥|ʊ̯|ʊ̰|ʌʌ|ʌː|ʌ̃|ʌ̆|ʌ̤|ʏʏ|ʏː|ʏ̃|a|e|i|o|u|y|æ|ø|œ|ɐ|ɑ|ɒ|ɔ|ɘ|ə|ɛ|ɜ|ɞ|ɤ|ɨ|ɪ|ɯ|ɵ|ɶ|ɿ|ʅ|ʉ|ʊ|ʌ|ʏ|ʮ|ʯ|ᴀ|r) ",
            " \\1 b \\3 ",
        ),
    },
    "d -> :null: / VL _ #": {
        "en": "the source, composed of the sound /d/, is deleted, when preceded by some sound of class VL (long vowel) and followed by a word boundary",
        "pt": "a fonte, composta pelo som /d/, é apagada, quando precedida por algum som da classe VL (vogal longa) e quando seguida por um delimitador de palavra",
        "fw": (
            " (ẽ̞ẽ̞|ø̞̃ø̞̃|ɔ̞̈ɔ̞̈|ɞ̞̃ɞ̞̃|ɯ̽̃ɯ̽̃|ãã|ẽẽ|e̞e̞|ẽ̞ː|ĩĩ|o̞o̞|õ̞ː|ỹỹ|æ̃æ̃|ø̃ø̃|ø̞ø̞|ø̞̃ː|œ̃œ̃|ɐ̃ɐ̃|ɐ̹ɐ̹|ɔ̞̈ː|ɛ̃ɛ̃|ɜ̃ɜ̃|ɞ̃ɞ̃|ɞ̞ɞ̞|ɞ̞̃ː|ɤ̞ɤ̞|ɤ̞̃ː|ɪ̃ɪ̃|ɪ̈ɪ̈|ɪ̈̃ː|ɯ̽ɯ̽|ɯ̽̃ː|ɵ̞ɵ̞|ɵ̞̃ː|ɶ̃ɶ̃|ʊ̃ʊ̃|ʊ̈ʊ̈|ʊ̈̃ː|ʏ̃ʏ̃|ãː|ẽː|e̞ː|e̹ː|ĩː|ḭː|õː|o̞ː|ũː|ỹː|æ̃ː|ø̃ː|ø̞ː|œ̃ː|ɐ̃ː|ɐ̹ː|ɑ̃ː|ɒ̃ː|ɔ̃ː|ɘ̃ː|ə̃ː|ɛ̃ː|ɜ̃ː|ɞ̃ː|ɞ̞ː|ɤ̃ː|ɤ̞ː|ɨ̃ː|ɪ̃ː|ɪ̈ː|ɯ̃ː|ɯ̽ː|ɵ̃ː|ɵ̞ː|ɶ̃ː|ʉ̃ː|ʊ̃ː|ʊ̈ː|ʌ̃ː|ʌ̯ː|ʏ̃ː|aa|aː|ee|eː|ii|iː|oo|oː|uu|uː|yy|yː|ææ|æː|øø|øː|œœ|œː|ɐɐ|ɐː|ɑɑ|ɑː|ɒɒ|ɒː|ɔɔ|ɔː|ɘɘ|ɘː|əə|əː|ɛɛ|ɛː|ɜɜ|ɜː|ɞɞ|ɞː|ɤɤ|ɤː|ɨɨ|ɨː|ɪɪ|ɪː|ɯɯ|ɯː|ɵɵ|ɵː|ɶɶ|ɶː|ʉʉ|ʉː|ʊʊ|ʊː|ʌʌ|ʌː|ʏʏ|ʏː) (d) (#) ",
            " \\1 \\3 ",
        ),
        "bw": (
            " (ẽ̞ẽ̞|ø̞̃ø̞̃|ɔ̞̈ɔ̞̈|ɞ̞̃ɞ̞̃|ɯ̽̃ɯ̽̃|ãã|ẽẽ|e̞e̞|ẽ̞ː|ĩĩ|o̞o̞|õ̞ː|ỹỹ|æ̃æ̃|ø̃ø̃|ø̞ø̞|ø̞̃ː|œ̃œ̃|ɐ̃ɐ̃|ɐ̹ɐ̹|ɔ̞̈ː|ɛ̃ɛ̃|ɜ̃ɜ̃|ɞ̃ɞ̃|ɞ̞ɞ̞|ɞ̞̃ː|ɤ̞ɤ̞|ɤ̞̃ː|ɪ̃ɪ̃|ɪ̈ɪ̈|ɪ̈̃ː|ɯ̽ɯ̽|ɯ̽̃ː|ɵ̞ɵ̞|ɵ̞̃ː|ɶ̃ɶ̃|ʊ̃ʊ̃|ʊ̈ʊ̈|ʊ̈̃ː|ʏ̃ʏ̃|ãː|ẽː|e̞ː|e̹ː|ĩː|ḭː|õː|o̞ː|ũː|ỹː|æ̃ː|ø̃ː|ø̞ː|œ̃ː|ɐ̃ː|ɐ̹ː|ɑ̃ː|ɒ̃ː|ɔ̃ː|ɘ̃ː|ə̃ː|ɛ̃ː|ɜ̃ː|ɞ̃ː|ɞ̞ː|ɤ̃ː|ɤ̞ː|ɨ̃ː|ɪ̃ː|ɪ̈ː|ɯ̃ː|ɯ̽ː|ɵ̃ː|ɵ̞ː|ɶ̃ː|ʉ̃ː|ʊ̃ː|ʊ̈ː|ʌ̃ː|ʌ̯ː|ʏ̃ː|aa|aː|ee|eː|ii|iː|oo|oː|uu|uː|yy|yː|ææ|æː|øø|øː|œœ|œː|ɐɐ|ɐː|ɑɑ|ɑː|ɒɒ|ɒː|ɔɔ|ɔː|ɘɘ|ɘː|əə|əː|ɛɛ|ɛː|ɜɜ|ɜː|ɞɞ|ɞː|ɤɤ|ɤː|ɨɨ|ɨː|ɪɪ|ɪː|ɯɯ|ɯː|ɵɵ|ɵː|ɶɶ|ɶː|ʉʉ|ʉː|ʊʊ|ʊː|ʌʌ|ʌː|ʏʏ|ʏː) (#) ",
            " \\1 d \\2 ",
        ),
    },
    # TODO: deal with the back reference with modifications, can be hard...
    "d|ɣ -> @1[+voiceless] / _ #": {
        "en": "the source, composed of either the sound /d/ or the sound /ɣ/, turns into the target, composed of the first matched sound (changed into a voiceless sound), when followed by a word boundary",
        "pt": "a fonte, composta pelo som /d/ ou pelo som /ɣ/, torna-se a meta, composta pelo primeiro som correspondente (mudado para um som voiceless), quando seguida por um delimitador de palavra",
        "fw": (" (d|ɣ) (#) ", " \\1[+voiceless] \\2 "),
        "bw": (" (\\1[+voiceless]) (#) ", " d|ɣ \\2 "),
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

        for rule, ref in sorted(REFERENCE.items()):
            ast = parser.parse(rule)
            en = english.compile(ast)
            assert en == ref["en"]

    def test_portuguese(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # Load sound changes and build the compiler
        SOUND_CLASSES = alteruphono.utils.read_sound_classes()
        portuguese = alteruphono.NLAutomata(SOUND_CLASSES, lang="pt")

        for rule, ref in sorted(REFERENCE.items()):
            ast = parser.parse(rule)
            pt = portuguese.compile(ast)
            assert pt == ref["pt"]

    def test_forward(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # Load sound changes and build the compiler
        SOUND_CLASSES = alteruphono.utils.read_sound_classes()
        forward = alteruphono.ForwardAutomata(SOUND_CLASSES)

        for rule, ref in sorted(REFERENCE.items()):
            ast = parser.parse(rule)
            fw = forward.compile(ast)
            assert fw == ref["fw"]

    def test_backward(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # Load sound changes and build the compiler
        SOUND_CLASSES = alteruphono.utils.read_sound_classes()
        backward = alteruphono.BackwardAutomata(SOUND_CLASSES)

        for rule, ref in sorted(REFERENCE.items()):
            ast = parser.parse(rule)
            bw = backward.compile(ast)
#            assert bw == ref["bw"]

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
