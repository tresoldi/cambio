AlteruPhono PEG Grammar
=======================

This directory holds the parser for AlteruPhono, generated from an
EBNF-notation with the [竜 TatSu](https://github.com/neogeny/TatSu) tool.

In normal operation, we would generate a Python parser with
`tatsu -o parser.py grammar.peg`, but this is currently failing (under
investigation). We are thus loading the grammar dynamically on the first
call to the object.

For visualization, the `pygraphviz` package must be installed beforehand,
along with `graphviz` itself. This is not necessary for ordinary operation.
To generate a visualization of the grammar, run:

```bash
tatsu -o grammar.png -d grammar.peg
```
