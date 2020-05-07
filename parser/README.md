AlteruPhono PEG Grammar
=======================

This directory holds the parser for AlteruPhono, generated from an
EBNF-notation with the [竜 TatSu](https://github.com/neogeny/TatSu) tool.

For manipulation, the `pygraphviz` package must be installed beforehand,
along with `graphviz` itself. This is not necessary for ordinary operation.

To generate the Python parser, run:

```bash
tatsu -o parser.py grammar.peg
```

To generate a visualization of the grammar, run:

```bash
tatsu -o grammar.png -d grammar.peg
```
