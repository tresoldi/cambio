import alteruphono
import csv


parser = alteruphono.parser.Parser()

rule_text = "S > p / _ V"
seq = "t i s e"
rule = alteruphono.old_parser.Rule(rule_text, parser(rule_text))
print(rule.ante)
print(rule.post)
alteruphono.forward(seq, rule)

with open("resources/sound_changes.tsv") as tsvfile:
    for row in csv.DictReader(tsvfile, delimiter="\t"):
        pass
#        print("==", [row['RULE']])
#
#        # build rule as in the previous model
#        ast = parser(row['RULE'])
#        rule = alteruphono.old_parser.Rule(row['RULE'], ast)
#
#        alteruphono.forward(row['TEST_ANTE'], rule)
#        alteruphono.backward(row['TEST_POST'], rule)
