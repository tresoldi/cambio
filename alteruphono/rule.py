# TODO: make just a dictionary? a data class? a named tuple?
class Rule:
    def __init__(self, rule_text, ast):
        self.source = rule_text
        self.ante = ast.ante
        self.post = ast.post

    # TODO: check if repr() and str() calls are needed
    def __repr__(self):
        return repr(self.source)

    def __str__(self):
        return str(self.source)

    def __hash__(self):
        return hash(self.source)


def make_rule(rule_text, parser):
    return Rule(rule_text, parser(rule_text))
