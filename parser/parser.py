import csv
import pprint
import json
import tatsu
from tatsu.util import asjson

def main():
    # Read and compile grammar
    with open("grammar.peg") as grammar:
        model = tatsu.compile(grammar.read())

    # Read sound changes
    with open("../resources/sound_changes.tsv") as tsvfile:
        rules = [row['RULE'] for row in  csv.DictReader(tsvfile, delimiter="\t")]

    TESTS = [
        ("arrow", [">", "->"]),
        ("slash", ["/", "//"]),
        ("empty", ["0", ":null:"]),
        ("focus", ["_"]),
        ("boundary", ["#", "$", "^"]),
        ("ipa", ["a", "ts", "*R"]),
        ("sequence", ["p a", "# ts *V _ r"]),
        ("feature_key", ["stop", "tier1"]),
        ("feature", ["stop", "-stop", "stop=true"]),
        ("feature_desc", ["[stop]", "*[feat1,-feat2,feat3=true]"]),
        ("backref", ["@1", "@1[+stop]", "*@2"]),
        ("sound_class", ["V", "*SV[+fricative]"]),
    ]

    for start, rules in TESTS:
        for rule in rules:
            ast1 = model.parse(rule, start=start)
            print("1", [rule], "--", [ast1], type(ast1))

            try:
                ast2 = model.parse(rule, start="segment")
                print("2", [rule], "--", [ast2], type(ast2))
            except:
                pass

    rule = "a p|b|#|V[+front]"
    ast1 = model.parse(rule, start="sequence")
    print("*", rule, "--", [ast1], type(ast1))
    pprint.pprint(ast1, indent=2, width=20)

#    for idx, a in enumerate(ast1.sequence):
#        print(idx, len(a), a)

#            print(type(ast))

    # to_python_sourcecode

def main2():
    GRAMMAR = """
    start = expr;

    expr = { segment }+;

#    segment = alternative | terminal ;
#    alternative = "|".{terminal}+;

    segment = "|".{@:terminal}+;

    terminal = r"x"|r"y";
    """

    model = tatsu.compile(GRAMMAR)
    ast = model.parse("x x|y y x|x|x|y")
    pprint.pprint(ast, indent=2, width=20)

if __name__ == '__main__':
    main()
