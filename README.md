# alteruphono

[![Build Status](https://travis-ci.org/tresoldi/alteruphono.svg?branch=master)](https://travis-ci.org/tresoldi/alteruphono)
[![codecov](https://codecov.io/gh/tresoldi/alteruphono/branch/master/graph/badge.svg)](https://codecov.io/gh/tresoldi/alteruphono)

`alteruphono` is a Python library for applying sound changes to phonetic and
phonological representations, intended for use in simulations of language
evolution.

*Please remember that `alteruphono` is a work-in-progress.*

In detail, with `alteruphono`:

    * List

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

## TODO

  - Use `logging` everywhere
  - Implement automatic, semi-automatic, and requested syllabification
    based on prosody strength
  - Implement both PEG grammars from separate repository
  - Add support for custom replacement functions (deciding on notation)

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

## References

abc

## Author

Tiago Tresoldi (tresoldi@shh.mpg.de)

The author was supported during development by the 
[ERC Grant #715618](https://cordis.europa.eu/project/rcn/206320/factsheet/en)
for the project [CALC](http://calc.digling.org)
(Computer-Assisted Language Comparison: Reconciling Computational and Classical
Approaches in Historical Linguistics), led by
[Johann-Mattis List](http://www.lingulist.de).

