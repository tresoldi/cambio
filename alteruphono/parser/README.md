AlteruPhono PEG Grammar
=======================

This directory holds the parser for AlteruPhono, generated from an
EBNF-notation with the [Arpeggio](https://textx.github.io/Arpeggio) library.

Upon change to grammar, run the stand-alone parser `parser.py`, defaulting
to debug mode, to generate the `.dot` files that can be used to generate
the `.png` files.

```bash`
$ dot -opeggrammar_parse_tree.png -Tpng peggrammar_parse_tree.dot
$ dot -opeggrammar_parser_model.png -Tpng peggrammar_parser_model.dot
```
