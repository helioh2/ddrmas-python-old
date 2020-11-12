from agent_sync_arguments import Rule, Literal, Term


class Builder:

    def __init__(self, agents_dict):
        self.agents_dict = agents_dict

    def build_rules(self, tuple_rule_list):
        return [self.build_rule(tuple_rule) for tuple_rule in tuple_rule_list]

    def build_rule(self, tuple_rule):
        id_ = tuple_rule[0]
        head = self.build_term(tuple_rule[1])
        body = [self.build_term(item) for item in tuple_rule[2]]
        return Rule(id_, head, body)

    def build_term(self, tuple_term):
        if tuple_term[0] in self.agents_dict.keys():
            definer = self.agents_dict[tuple_term[0]]
        else:
            definer = tuple_term[0]

        literal = self.build_literal(tuple_term[1])

        return Term(definer, literal)

    def build_literal(self, string_literal):
        negative = string_literal[0] == "¬"
        symbol = string_literal[1:] if negative else string_literal
        return Literal(symbol, negative)
