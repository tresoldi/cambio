# alteruphono

[![Build Status](https://travis-ci.org/tresoldi/alteruphono.svg?branch=master)](https://travis-ci.org/tresoldi/alteruphono)
[![codecov](https://codecov.io/gh/tresoldi/alteruphono/branch/master/graph/badge.svg)](https://codecov.io/gh/tresoldi/alteruphono)

`alteruphono` is a Python library for applying sound changes to phonetic and
phonological representations, intended for use in simulations of language
evolution.

*Please remember that `alteruphono` is a work-in-progress.*

## Installation

In any standard Python environment, `alteruphono` can be installed with:

```
pip install alteruphono
```

The `pip` installation with also fetch dependencies, such as `pyclts`,
if necessary. Installation in virtual environments is recommended.

## How to use

Sound sequences are to be given in common
[CLDF](https://cldf.clld.org/)/[LingPy](http://lingpy.org) notation, i.e.,
as a single string with single space-separated graphemes. The library supports
different transcription systems, defaulting BIPA as defined
in [pyclts](https://pypi.org/project/pyclts/).

Sound changes are defined by simplified regular expressions. Check
the `resources/sounds_changes.tsv` for an example.

A basic usage, drawing a random sound change from the default collection
and applying it, is:

```python
import alteruphono

rules = alteruphono.utils.read_sound_changes()
random_rules = [alteruphono.utils.random_change(rules) for r in range(3)]
for rule in random_rules:
    source = rule["source"]
    target = rule["target"]
    test_case = rule["test"].split("/")[0].strip()

    print("%s -> %s" % (source, target))
    print("  [%s] [%s]" % (test_case, alteruphono.apply_rule(test_case, source, target)))
```

returning:

```
V N C -> @1[+nasalized] @3
  [a b ts a r i m b s u] [a b ts a r ĩ b s u]
e i -> a i
  [d i a z e i l e n] [d i a z a i l e n]
n k|g -> ŋ @2
  [a k a n k m i k s] [a k a ŋ k m i k s]
```

## TODO

For version 2.0:
    - Implement mapper support in the automata (also with test cases)
    - Implement parentheses support in the grammar and automata (also with
      test cases)
    - Consider moving to ANTLR
    - For the grammar, consider removing direct sound match in `segment`,
      only using `alternative` (potentially renamed to `expression` and dealt
      with in an appropriate way)
    - don't collect a `context`, but `left` and `right` already in the
      AST (i.e., remove the `position` symbol)

    - In Graphviz output
        - Accept a strng with a description (could be the output of the
          NLAutomata)
        - Draw borders around `source`, `target`, and `context`
        - Add indices to sequences, at least optionally
        - Accept definitions of sound classes and IPA, at least in English

Old version

  - Use `logging` everywhere
  - Implement automatic, semi-automatic, and requested syllabification
    based on prosody strength
  - Implement both PEG grammars from separate repository
  - Add support for custom replacement functions (deciding on notation)

## Manual

There are two basic elements: rules and sequences. A rule operates on
a sequence, resulting in a single, potentially different, sequence in
forwards direction, and in at least one, potentially different, sequence
in backwards direction.

Following the conventions and practices of CLTS, CLDF, Lingpy,
and orthographic profiles, the
proposed notation operates on "strings", that is, text in Unicode
characters representing a sequence of one or more segments separated
by spaces. The most common segments are sounds as represented by Unicode
glyphs, so that a transcription like /haʊs/ ("house" in English Received
Pronounciation) is represented as `"h a ʊ s"`, that is, not considering
spaces, U+0068 (LATIN SMALL LETTER H),
U+0061 (LATIN SMALL LETTER A),
U+028A (LATIN SMALL LETTER UPSILON), and U+0073
(LATIN SMALL LETTER S). The usage of spaces might seem inconventient and
even odds at first, but the convention has proven useful with years of
experience of phonological transcription for computer-assisted treatment, as
not only it makes no automatic assumption of what constitutes a segment
(for example, allowing user to work with fully atomic syllables), but
facilitates validation work.

A `rule` is a statement expressed in the `A > B / C _ D` notation, where
C and D, both optional, express the preceding and following context.
It is a shorthand to common notation, internally mapped to
`C A D > B A D`. While A and B might expresses something different from
historical evolution, such as correspondence, they are respectively named
`ante` and `post`, and the rule can be real as "the sequence of segments
A changes into the sequence of sounds B when preceded by C and followed by
D".
A, B, and C are referred as as "sequences", and are composed of one or
more "segments". A "segment" is the basic, fundamental, atomic unit of a
sequence. 

Segments can be of X types:

  - sound segments, such as phonemes (like `a` or `ʒ`) or whatever is
    defined as an atomic segment by the used (for example, full-length
    syllables such as `ba` or `ʈ͡ʂʰjou̯˨˩˦`). In most cases, a phonetic or
    phonological transcription system such IPA or NAPA will be used; by
    default, the system operates on BIPA, which also facilitates
    normalization in terms of homoglyphs, etc.
  - A bundle of features, expressed as comma separated feature-values
    enclosed by square brackets, such as `[consonant]`, referring to all
    consonants, `[unrounded,open-mid,central,vowel]`, referring to all
    sounds matching this bundle of features (that is, `ɜ` and the same
    sound with modifiers), etc. Complex relationships and tiers allow to
    expressed between segments, as described later. By default, the system
    of descriptors used by BIPA is used.
  - Sound-classes, which are common short-hands for bundles of features,
    such as `K` for `[consonant,velar]` or `R` for "resonants" (defined
    internally as `[consonant,-stop]`). A default system, expressed in
    table X, is provided, and can be replaced, modified, or extended by the
    user. Sound-classes are expressed in all upper-case. 
  - Back-references, used to refer to other segments in a sequence,
    which are expressed by the at-symbol (`@`) and a
    numeric index, such as `@1` or `@3` (1-based). These will are better
    explored in X.
  - Special segments related to sequences, which are
    - `_` (underscore) for the "focus" in a context (from the name by
      Hartman 2003), that is, the position where `ante` and `post` sequences
      are found
    - `#` (hash) for word boundaries
    - `.` (dot) for syllable breaks

Sound segments, sound-classes, and back-references can carry a modifier,
which is following bundle of features the modifies the value expressed or
referred to. For example `θ[voiced]` is equivalent to `ð`, `C[voiceless]`
would match only voiceless consonants, `C[voiceless] ə @1[voiced]` would
match sequences of voiceless consonants, followed by a schwa, followed by
the corresponding voiced consonant (thus matching sequences like `p ə b`
and `k ə g`, but not `p ə g`).

Other non primitives include alternatives and sets.

## How to cite

If you use `alteruphono`, please cite it as:

> Tresoldi, Tiago (2019). Alteruphono, a tool for simulating sound changes.
Version 0.0.1dev. Jena. Available at: https://github.com/tresoldi/alteruphono

In BibTex:

```
@misc{Tresoldi2019alteruphono,
  author = {Tresoldi, Tiago},
  title = {Alteruphono, a tool for simulating sound changes},
  howpublished = {\url{https://github.com/tresoldi/alteruphono}},
  address = {Jena},
  year = {2019},
}
```

## Author

Tiago Tresoldi (tresoldi@shh.mpg.de)

The author was supported during development by the 
[ERC Grant #715618](https://cordis.europa.eu/project/rcn/206320/factsheet/en)
for the project [CALC](http://calc.digling.org)
(Computer-Assisted Language Comparison: Reconciling Computational and Classical
Approaches in Historical Linguistics), led by
[Johann-Mattis List](http://www.lingulist.de).

