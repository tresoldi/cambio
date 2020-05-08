import alteruphono
import csv
import pprint

debug = False
pp = pprint.PrettyPrinter(indent=4)

import arpeggio
from arpeggio.cleanpeg import ParserPEG

class Visitor(arpeggio.PTNodeVisitor):
    def visit_op_feature(self, node, children):
        return {'feature':children[1], 'value':children[0]}

    def visit_modifier(self, node, children):
        # don't collect square brackets
        return list(children[1])

    def visit_focus(self, node, children):
        return {'focus':node.value}

    def visit_choice(self, node, children):
        return list(children)

    def visit_boundary(self, node, children):
        return {'boundary':node.value}

    def visit_empty(self, node, children):
        return {'empty':node.value}

    def visit_backref(self, node, children):
        # return only the index as integer, along with any modifier
        if len(children) == 2:
            return {'backref':int(children[1])}
        else:
            return {'backref':int(children[1]), 'modifier':children[2]}

    def visit_sound_class(self, node, children):
        return {'sound_class':node.value}

    def visit_grapheme(self, node, children):
        return {'grapheme':node.value}

    # Don't capture `arrow`s
    def visit_arrow(self, node, children):
        pass

    # Don't capture `slash`es
    def visit_slash(self, node, children):
        pass

    # Sequences
    def visit_ante(self, node, children):
        return {'ante':list(children)}
    def visit_post(self, node, children):
        return {'post':list(children)}
    def visit_context(self, node, children):
        return {'context': list(children)}

    # Entry point
    def visit_rule(self, node, children):
        # Combine all subsquences, dealing with context optionality
        ret = {}
        for seq in children:
            ret.update(seq)

        return ret

grammar = open('sound_change.peg', 'r').read()
parser = ParserPEG(grammar, 'rule', ws='\t ', debug=debug)

with open("resources/sound_changes.tsv") as tsvfile:
    for row in csv.DictReader(tsvfile, delimiter="\t"):
        if "-a" in row['RULE']:
            continue
        print("==", [row['RULE']])

        parse_tree = parser.parse(row['RULE'])
        pprint.pprint(parse_tree)
        content = arpeggio.visit_parse_tree(parse_tree, Visitor())
        pp.pprint(content)
        print()
