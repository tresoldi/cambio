import alteruphono
import csv
import pprint

parser = alteruphono.parser.Parser()

with open("resources/sound_changes.tsv") as tsvfile:
    for row in csv.DictReader(tsvfile, delimiter="\t"):
        print("==", [row])

        ast = parser(row['RULE'])
        print(ast)
        rule = alteruphono.old_parser.Rule(row['RULE'], ast)
        alteruphono.forward(row['TEST_ANTE'], rule)
