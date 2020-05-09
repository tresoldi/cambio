import alteruphono
import csv
import pprint

parser = alteruphono.parser.Parser()

#with open("resources/sound_changes.tsv") as tsvfile:
#    for row in csv.DictReader(tsvfile, delimiter="\t"):
#        print("==", [row])

rule_text = 'd|ɣ -> @1[+voiceless] / _ #'
ast = parser(rule_text)
print(ast)
rule = alteruphono.old_parser.Rule(rule_text, ast)
ret = alteruphono.backward('a d j aː t', rule)
print(ret)
