
class ComparableObject:
    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

class Literal(ComparableObject):

    def __init__(self, symbol, negative=False):
        self.symbol = symbol
        self.negative = negative

    def __neg__(self):
        return Literal(self.symbol, not self.negative)


class Term(ComparableObject):

    def __init__(self, definer, literal):
        self.definer = definer
        self.literal = literal

    def __neg__(self):
        return Term(self.definer, - self.literal)


class Rule(ComparableObject):

    def __init__(self, id, head, body):
        self.head = head
        self.body = body

    def __str__(self):
        return self.head + " <-- " + self.body


class StaticRule(Rule):
    pass


class Context(ComparableObject):

    def __init__(self, id, focus_rules):
        self.id = id
        self.focus_rules = focus_rules


class MultiAgentSystem(ComparableObject):

    def __init__(self, similarity_threshold=0):
        self.similarity_threshold = similarity_threshold


class Answer(ComparableObject):

    def __init__(self, queried_term, context, equivalent_term, truth_value, blocking_set, support_set):
        self.queried_term = queried_term
        self.context = context
        self.equivalent_term = equivalent_term
        self.truth_value = truth_value
        self.support_set = support_set
        self.blocking_set = blocking_set


def get_next_from_hist(hist, term):
    index = hist.index(term)
    return hist[index+1]


class Agent(ComparableObject):

    def __init__(self, system, rules):
        self.system = system
        self.rules = rules


    def query(self, sender, term, context, hist=[]):
        extended_rules = self.create_extended_rules(context.focus_rules)
        equivalent_term = self.look_for_similar_term(term, extended_rules)
        if not equivalent_term:
            return Answer(term, context, None, "False", [], [])
        if equivalent_term in hist:
            return Answer(term, context, equivalent_term, "Undefined", [get_next_from_hist(hist, equivalent_term)], [])
        hist_q = hist + [equivalent_term]

        if self.local_ans(equivalent_term, extended_rules):
            return Answer(term, context, equivalent_term, "True", [], [])
        if self.local_ans(- equivalent_term, extended_rules):
            return Answer(term, context, equivalent_term, "False", [], [])

        unblocked_q, supported_q, blocking_set_q, support_set_q = self.find_support(
            equivalent_term, extended_rules, context, hist_q
        )
        if not unblocked_q:"False"
            return Answer(term, context, equivalent_term, "False", [], [])

        if - equivalent_term in hist:
            unblocked_neg_q = True
            supported_neg_q = False
            blocking_set_neg_q = [get_next_from_hist(hist, - equivalent_term)]
            support_set_neg_q = []
        else:
            hist_neg_q = hist + [- equivalent_term]
            unblocked_neg_q, supported_neg_q, blocking_set_neg_q, support_set_neg_q = self.find_support(
                - equivalent_term, extended_rules, context, hist_neg_q
            )

        if supported_q and (unblocked_neg_q or self.stronger(support_set_q, blocking_set_neg_q) == support_set_q):
            return Answer(term, context, equivalent_term, "True", blocking_set_q, support_set_q)
        elif supported_neg_q and (not unblocked_q or self.stronger(blocking_set_q, support_set_neg_q) != blocking_set_q):
            return Answer(term, context, equivalent_term, "False", blocking_set_q, support_set_q)
        else:
            return Answer(term, context, equivalent_term, "Undefined", blocking_set_q, support_set_q)



    def create_extended_rules(self, focus_rules):
        converted_focus_rules = [self.convert_focus_rule_to_local(rule) for rule in focus_rules]
        return set(self.rules) + set(converted_focus_rules)

    def convert_focus_rule_to_local(self, rule):
        return Rule(self.convert_term_to_local(rule.head), [self.convert_term_to_local(term) for term in rule.body])

    def convert_term_to_local(self, term):
        return Term(self, term.literal)

    def look_for_similar_term(self, term, rules):
        for rule in rules:
            if self.similar_enough(rule.head, term):
                return rule.head
        return False

    def local_ans(self, term, extended_rules):
        rules_p = [rule for rule in extended_rules if isinstance(rule, StaticRule) and rule.head == term]
        for rule in rules_p:
            if all(self.local_ans(b, extended_rules) for b in rule.body):
                return True
        return False

    def find_support(self, term, extended_rules, context, hist_p):
        rules_p = [rule for rule in extended_rules if rule.head == term]
        supported_p = unblocked_p = False
        support_set_p = blocking_set_q = []
        for rule in rules_p:
            cycle_r = False
            support_set_r = blocking_set_r = []


    def process_body(self, rule, context, hist_p):
        for body_member in rule.body:
            ans_b, support_set_r, blocking_set_r, cycle_r = self.process_body_member(
                body_member, rule, context, hist_p
            )
            if not ans_b:
                return False



