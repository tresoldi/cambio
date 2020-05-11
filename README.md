# alteruphono

[![Build Status](https://travis-ci.org/tresoldi/alteruphono.svg?branch=master)](https://travis-ci.org/tresoldi/alteruphono)
[![codecov](https://codecov.io/gh/tresoldi/alteruphono/branch/master/graph/badge.svg)](https://codecov.io/gh/tresoldi/alteruphono)

`alteruphono` is a Python library for applying sound changes to phonetic and
phonological representations, intended for use in simulations of language
evolution.

*Please remember that, while usable, `alteruphono` is a work-in-progress.
The best documentation is currently to check the tests, and the
library is not recommended for production usage.*

## Future improvements

- Move from existing AST to a dictionary, mostly for speed and portability
  (even if it might be the code more verbose); should still be a frozen
  dictionary
- Memoize `parser.__call__()` calls
- Consider that, if a rule has alternatives, sound_classes, or other
  profilific rules in `context`, it might be necessary to
  perform a more complex merging and add back-references in
  `post` to what is matched in `ante`, which could potentially
  even mean different ASTs for forward and backward. This
  needs further and detailed investigation, or explicit
  exclusion of such rules (the user could always have the
  profilic rules in `ante` and `post`, manually doing what
  would be done here).
- Use logging where appropriate

## Installation

In any standard Python environment, `alteruphono` can be installed with:

```
pip install alteruphono
```

## How to use

Detailed documentation can be found in the library source code and will
be published along with the paper accompanying the library; terser
technical description is available at the end of this document.
Consultation of the
[sound changes provided for testing purposes](https://github.com/tresoldi/alteruphono/blob/master/resources/sound_changes.tsv)
is also recommended.

For basic usage as a library, the `.forward()` and `.backward()` functions
can be used as a wrapper for most common circumstances. In the
examples below, a rule `p > t / _ V` (that is, /p/ turns into /t/ when
followed by a vowel) is applied both in forward and backward direction
to the `/pate/` sound sequence; the `.backward()` function correctly
returns the two possible proto-forms:

```python
>>> import alteruphono
>>> alteruphono.forward("# p a t e #", "p > t / _ V")
['#', 't', 'a', 't', 'e', '#']
>>> alteruphono.backward("# p a t e #", "p > t / _ V")
[['#', 'p', 'a', 't', 'e', '#'], ['#', 'p', 'a', 'p', 'e', '#']]
```

A stand-alone command-line tool can be used to call these wrapper
functions:

```bash
$ alteruphono forward "# p a t e #" "p > t / _ V"
# t a t e #
$ alteruphono backward "# p a t e #" "p > t / _ V"
['# p a t e #', '# p a p e #']
```

## Elements

We are not exploring every detail of the formal grammar for annotating
sound changes, such as the flexibility with spaces and tabulations or
equivalent symbols for the arrows; for full information, interested parties
can consult the reference PEG grammar and the source code.

AlteruPhono operates by applying ordered lists of sound changes to
textual representation of sound sequences.

Sound changes are annotated in the `A -> B / C` syntax,
whose constituents are
for reference
referred as "source" (A), "target" (B), and "context" (C), with the
first two being mandatory; the other elements are named "arrow" and
"slash". When applied to segment sequences, we refer to the original
one as "ante" and to the resulting one (which might have been modified
or not) as "post". So, with a rule "p -> b / _ a" applied to "pape":

- `p` is the "source"
- `b` is the "target"
- `_ a` is the "context"
- "pape" is the "ante (sequence)"
- "bape" is the "post (sequence)"

Note that, if applied backwards, a rule will have a post sequence but
potentially more than one ante sequence. If the rule above is applied
backwards to the post sequence "bape", as explained in the backwards
definition and given that we have no complementary information, the
result is a set of ante sequences "pape" and "bape".

AlteruPhono operates on sound sequences expressed in standard
[CLDF](https://cldf.clld.org/)/[LingPy](http://lingpy.org) notation,
derived for Cysouw work,
i.e., as a string character string with tokens separated by single spaces.
As such, a word like the English "chance" is represented not as
"`/tʃæns/`" or `/t͡ʃæns/`, in proper IPA notation, but as "`tʃ æ n s`".
While the notation might at first seem strange, it has proven its
advantages with extensive work on linguistic databases, as it not only
facilitates data entry and inspection, but also makes no assumptions about
what constitutes a segment, no matter how obvious the segmentation might
look to a linguist. On one had, being agnostic in terms of the segmentation
allows the program to operate as a "dumb" machine, and on the other allows
researchers to operate on different kinds of segmentation if suitable for
their research, including treating whole syllables as segments. In order
to facilitate the potentially tedious and error-prone task of manual
segmentation, orthographic profiles can be used as in Lexibank.


## Catalogs

While they are not enforced and in some cases are not needed, such as
when the system operates as a glorified search&replace, alteruphono is
designed to operate with three main catalogs: graphemes, features, and
segment classes.

Graphemes are sequences of one or more textual characters where most
characters are accepts (exceptions are...).
While in most cases it will correspond
to common transcription system such as the IPA, and in most case correspond
to a single sound or phoneme, this is not enforced and sequence of
characters (with the exception of a white-space, a tabulation, a forward
slash, square and curly brackets, and an arrow) can be used to represent
anything defined as
a segment in a corresponding catalog. Also note that the slash notation
of Lexibank is supported. The default catalog distributed with alteruphono
is based on the BIPA system of clts.

Features are descriptors... Default is derived from BIPA descriptors,
mostly articulatory, but we also incluse some distinctive feature
systems.

It is not necessary for a grapheme catalog to specify the features that
compose each grapheme, but this severly limits the kind of operations
possible, particularly when modelling observed or plausible sound
changes.

The default catalogs are derived from BIPA... such as in examle

Segment classes are just shorthards. The default distributed with AlteruPhono
includes a number of shorthands common in the literature and mostly
unambiguous

## Types

- A **grapheme** is a sequence of one or more textual characters representing
a segment, such as "`a`", "`kʷʰ`".

- A **bundle** is an explicit listing of features and values, as defined
in a reference, enclosed in square brackets, such as
"`[open,front,vowel]`" or "`[-vowel]`". Features are separated by commas,
with optional spaces, and may carry a specific value in the format
`feature=value` with `value` being either a logical boolean ("true" or
"false") or a numeric value; shorthands for "true" and "false" are
defined as the operators "+" and "-"; if no "value" is provided, it defaults
to "true" (so that `[open,front,vowel]` is internally translated to
`[open=true,front=true,vowel=true]`). Note on back-references here
(experimental)

- A **modifier** is a bundle of feautes used to modify a basic value;
for example, if "V" defines a segment class (see item below) of vowels,
"V[long]" would restrict the set of matched segments to long vowels.

- A **segment-class** is a short-hand to a bundle of features, as defined
in a reference, intended to match one or more segments are expressed with
one or more upper-case characters, such as "C" or
"VL" (for [consonant] and [long,vowel], respectively, in the
default). A segment class can have a modifier.

- A **marker** is a single character non-segmental information. Defined
markers are # for word-boundary, . for syllable break, + for morpheme
boundary, stress marks and tone marks. Note that some markers,
particularly suprasegmental features as stress and tone, in most cases
will not be referred directly when writing rule, but by tiers. See
section on tiers.

- A **focus** is a special marker, represented by underscore, and used in
context to indicate the position of the source and target. See reference
when discuss contexts.

- An **alternative** is a list of one or more segments (which tzype?)
separated by a vertical bar, such "b|p". While in almost all cases of
actual usage alternatives could be expressed by bundles (such
"b|p" as "[plosive,bilabial]" in most inventories, using an alternative is
in most cases preferable for legibility

- A **set** is a list of alternative segments where the order is
significant, expressed between curly brackets and separated by commas,
such as `{a,e}`. The order is significant in the sense that, in the
case of a corresponding set, elements will be matched by their index:
if `{a,e}` is matched with `{ɛ,i}`, all /a/ will become /ɛ/ and all
/e/ will become /i/ (note how, with standard IPA descriptors, it would
not be possible to express such raising in a an unambiguos way)

- A **back-reference** is a reference to a previously matched segment,
expressed by the symbol @ and the numeric index for the segment,
(such as @2 for referring to the second element,
the vowel /a/, in the segment sequence "b a"). As such, back-references
allow to carry identities: if "V s V" means any intervocalic "s" and
"a s a" means only "s" between "a", "V s @1" means any "s" in
intervocalic position where the two vowels are equal. Back-references
can take modifier.



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

> Tresoldi, Tiago (2020). Alteruphono, a tool for simulating sound changes.
Version 0.3. Jena. Available at: https://github.com/tresoldi/alteruphono

In BibTex:

```
@misc{Tresoldi202alteruphono,
  author = {Tresoldi, Tiago},
  title = {Alteruphono, a tool for simulating sound changes. Version 0.3.},
  howpublished = {\url{https://github.com/tresoldi/alteruphono}},
  address = {Jena},
  year = {2020},
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
