import itertools
from collections import deque
from enum import Enum, auto
from typing import List, Tuple, Union


class TruthValue(Enum):
    TRUE = auto()
    FALSE = auto()
    UNDEFINED = auto()


def equal_dicts_except(dict1, dict2, except_=()):
    if set(dict1.keys()) != set(dict2.keys()):
        return False
    return all(dict1[field_name] == dict2[field_name] for field_name in dict1.keys() if field_name not in except_)


class ComparableObjectOld:
    def __eq__(self, other):
        if type(other) is type(self):
            return equal_dicts_except(self.__dict__, other.__dict__, ("id",))
        return False


class ComparableObject:

    def _key(self):
        return tuple([attr_value for attr_value in self.__dict__.values()])

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._key() == other._key()
        return NotImplemented


class Literal(ComparableObject):

    def __init__(self, symbol, positive=True):
        self.symbol = symbol
        self.positive = positive

    def __neg__(self):
        return Literal(self.symbol, not self.positive)


class Term(ComparableObject):

    def __init__(self, definer, literal):
        self.definer = definer
        self.literal = literal

    def __neg__(self):
        return Term(self.definer, - self.literal)

    def has_instantiated_term_in(self, list_):
        if self.definer != "X":
            return False
        return any(term.original_literal == self.literal for term in list_)

    def _key(self):
        return self.definer, self.literal

class InstantiatedTerm(Term):

    def __init__(self, definer, literal, original_literal, sim_degree):
        super().__init__(definer, literal)
        self.original_literal = original_literal
        self.sim_degree = sim_degree


class Rule(ComparableObject):

    def __init__(self, id_, head, body):
        self.id = id_
        self.head = head
        self.body = body

    def __str__(self):
        return self.head + " <-- " + self.body

    def _key(self):
        return self.head, tuple(self.body)


class StaticRule(Rule):
    pass


class QueryContext(ComparableObject):

    def __init__(self, id_, term, agent, focus_knowledge):
        self.id = id_
        self.term = term
        self.agent = agent
        self.focus_knowledge = focus_knowledge

    def _key(self):
        return self.id


class MultiAgentSystem(ComparableObject):

    def __init__(self, similarity_function=lambda term1, term2: term1 == term2, similarity_threshold=0):
        self.similarity_threshold = similarity_threshold
        self.similarity_function = similarity_function
        self.agents = dict()
        self.query_contexts = dict()

        self.query_context_id_generator = ("q" + str(n) for n in itertools.count(start=0))

    def similar_enough(self, sim_degree):
        return sim_degree >= self.similarity_threshold

    def similarity(self, term1, term2):
        return self.similarity_function(term1, term2)

    def new_query_context(self, term, agent, focus_knowledge):
        new_id = next(self.query_context_id_generator)
        new_query_context = QueryContext(new_id, term, agent, focus_knowledge)
        self.query_contexts[new_id] = new_query_context
        return new_query_context

class Answer(ComparableObject):

    def __init__(self, queried_term, context, equivalent_term, truth_value, arg_tree):
        self.queried_term = queried_term
        self.context = context
        self.equivalent_term = equivalent_term
        self.truth_value = truth_value
        self.arg_tree = arg_tree


def get_next_from_hist(hist, term):
    index = hist.index(term)
    return hist[index+1]


def hist_after_element(hist: list, element):
    index_element = hist.index(element)
    return hist[index_element+1:]


class SummarizedArgument:

    def __init__(self, conclusion: Term, foreign_leaves: List[InstantiatedTerm] = None):
        self.conclusion = conclusion
        self.foreign_leaves = foreign_leaves


class ArgTree(object):

    def __init__(self, parent: SummarizedArgument = None, children: List["ArgTree"] = None, is_promise: bool = False):
        self.parent = parent
        self.children = children if children is not None else list()
        self.is_promise = is_promise

    def get_all_foreign_leaves(self):
        children_foreign_leaves = set()
        for child in self.children:
            children_result_set = children_foreign_leaves.union(child.get_all_foreign_leaves())
        return set(self.parent.foreign_leaves).union(children_result_set)

    def add_child(self, tree: "ArgTree"):
        self.children.append(tree)


def arg_tree_promise_for(term):
    arg = SummarizedArgument(term)
    return ArgTree(arg, None, True)


def arg_tree_leaf_for(term):
    arg = SummarizedArgument(term)
    return ArgTree(arg, None, False)


class Agent(ComparableObject):

    def __init__(self, id_, system):
        self.id = id_
        self.system = system
        self.rules = []
        self.preference_function = dict()
        self.query_memory = dict()
        self.known_agents = self.system.agents.values()

    def initialize_query(self, term, focus_knowledge):
        context = self.system.new_query_context(term, self, focus_knowledge)
        return self.query(self, term, context, [])

    def query(self, sender: "Agent", term: Term, context: QueryContext, hist: List[InstantiatedTerm] = []):

        extended_rules = self.create_extended_rules(context.focus_knowledge)
        equivalent_term = self.look_for_similar_term(term, extended_rules)

        if equivalent_term is None:
            return Answer(term, context, None, TruthValue.FALSE, None)
        if self.local_ans(equivalent_term, extended_rules):
            return Answer(term, context, equivalent_term, TruthValue.TRUE, arg_tree_leaf_for(equivalent_term))
        if self.local_ans(- equivalent_term, extended_rules):
            return Answer(term, context, equivalent_term, TruthValue.FALSE, None)

        if equivalent_term in hist:
            # return Answer(term, context, equivalent_term, TruthValue.UNDEFINED, arg_tree_promise_for(equivalent_term))
            _, _, arg_tree_q = self.query_agents([equivalent_term.definer], equivalent_term, context, hist)
            ## a ideia aqui é que se já estava no historico, então o agente em questão já possui em sua query_memory
            ## a argumentation tree
            unblocked_q = True
            supported_q = False
        else:
            hist_q = hist + [equivalent_term]

            unblocked_q, supported_q, arg_tree_q = self.find_support(
                equivalent_term, extended_rules, context, hist_q
            )
            if not unblocked_q:
                return Answer(term, context, equivalent_term, TruthValue.FALSE, None)

        if (- equivalent_term).has_instantiated_term_in(hist):
            _, _, arg_tree_neg_q = self.query_agents([(-equivalent_term).definer], -equivalent_term, context, hist)
            ## a ideia aqui é que se já estava no historico, então o agente em questão já possui em sua query_memory
            ## a argumentation tree
            unblocked_neg_q = True
            supported_neg_q = False
        else:
            hist_neg_q = hist + [- equivalent_term]
            unblocked_neg_q, supported_neg_q, arg_tree_neg_q = self.find_support(
                - equivalent_term, extended_rules, context, hist_neg_q
            )

        if supported_q and (not unblocked_neg_q or self.stronger(arg_tree_q, arg_tree_neg_q) == arg_tree_q):
            return Answer(term, context, equivalent_term, TruthValue.TRUE, arg_tree_q)
        elif supported_neg_q and (not unblocked_q or self.stronger(arg_tree_q, arg_tree_neg_q) != arg_tree_q):
            return Answer(term, context, equivalent_term, TruthValue.FALSE, arg_tree_q)
        else:
            return Answer(term, context, equivalent_term, TruthValue.UNDEFINED, arg_tree_q)

    def create_extended_rules(self, focus_knowledge) -> List[Rule]:
        converted_focus_knowledge = [self.convert_focus_rule_to_local(rule) for rule in focus_knowledge]
        return set(self.rules).union(set(converted_focus_knowledge))

    def convert_focus_rule_to_local(self, rule: Rule) -> Rule:
        return Rule(
            rule.id + "_" + self.id,
            self.convert_term_to_local(rule.head),
            [self.convert_term_to_local(term) for term in rule.body])

    def convert_term_to_local(self, term: Term) -> Term:
        return Term(self, term.literal)

    def look_for_similar_term(self, term: Term, rules: List[Rule]) -> InstantiatedTerm:
        for rule in rules:
            sim_degree = self.similarity(rule.head, term)
            if self.similar_enough(sim_degree):
                return InstantiatedTerm(rule.head.definer, rule.head.literal, term.literal, sim_degree)
        return None

    def similar_enough(self, sim_degree):
        return self.system.similar_enough(sim_degree)

    def local_ans(self, term: Term, extended_rules: List[Rule]) -> bool:
        rules_p = [rule for rule in extended_rules if isinstance(rule, StaticRule) and rule.head == term]
        for rule in rules_p:
            if all(self.local_ans(b, extended_rules) for b in rule.body):
                return True
        return False

    def find_support(self,
                     term: Term,
                     extended_rules: List[Rule],
                     context: QueryContext,
                     hist_p: List[InstantiatedTerm]
    ) -> Tuple[bool, bool, ArgTree]:

        rules_p = [rule for rule in extended_rules if rule.head == term]
        supported_p = unblocked_p = False
        arg_tree_p = ArgTree(SummarizedArgument(term))
        results_found = dict()

        for rule in rules_p:
            result_body_members = self.process_body_members(rule, context, hist_p)
            if not result_body_members:
                continue
            results_found[rule.id] = result_body_members

        for rule_id, (arg_tree_r, cycle_r) in results_found.items():
            if supported_p and cycle_r:
                continue   # estrategia que busca sempre resultados mais positivos, buscando ignorar os ciclos
            if not unblocked_p or self.stronger(arg_tree_p, arg_tree_r) == arg_tree_r:
                arg_tree_p = arg_tree_r
            unblocked_p = True
            if not cycle_r:
                supported_p = True

        return unblocked_p, supported_p, arg_tree_p

    def process_body_members(self,
                             rule: Rule,
                             context: QueryContext,
                             hist_p: List[InstantiatedTerm]
                             ) -> Union[Tuple[ArgTree, bool], bool]:

        cycle_r = False
        arg_tree_r = ArgTree(SummarizedArgument(rule.head))

        for body_member in rule.body:

            if body_member.definer not in self.known_agents:
                body_inst, tv_b, arg_tree_b = self.query_agents(self.known_agents + [self], body_member, rule,
                                                                 context, hist_p)
            else:
                body_inst, tv_b, arg_tree_b = self.query_agents([body_member.definer], body_member, rule,
                                                                 context, hist_p)

            if tv_b == TruthValue.FALSE:
                return False

            cycle_r = cycle_r or tv_b == TruthValue.UNDEFINED
            if body_inst.definer != self:
                arg_tree_r.add_child(arg_tree_b)

        return arg_tree_r, cycle_r


    def query_agents(self,
                    agents: List["Agent"],
                    term: Term,
                    context: QueryContext,
                    hist_p: List[InstantiatedTerm]
                    ) -> Tuple[InstantiatedTerm, TruthValue, ArgTree]:

        term_inst = None
        tv_b = TruthValue.FALSE
        arg_tree_b = ArgTree()

        for agent in agents:
            if (context.id, term, agent.id) in self.query_memory.keys():
               term_aux, tv_aux, arg_tree_aux = self.query_memory[(context.id, term, agent.id)]
            else:
               answer = agent.query(self, term, context, hist_p)  # TODO: async
               term_aux, tv_aux, arg_tree_aux = answer.equivalent_term, answer.truth_value, answer.arg_tree
               self.query_memory[(context.id, term, agent.id)] = term_aux, tv_aux, arg_tree_aux

            if tv_aux == TruthValue.FALSE:
               continue
            # if agent != self:
            #     arg_tree_aux = arg_tree_aux + []
            sim = self.similarity(term, term_aux)
            if (
                   tv_aux == TruthValue.UNDEFINED and tv_b != TruthValue.TRUE and
                   (arg_tree_b == ArgTree() or self.stronger(arg_tree_b, arg_tree_aux) != arg_tree_b)
            ):

               tv_b = TruthValue.UNDEFINED
               term_inst = InstantiatedTerm(agent, term_aux, term, sim)
               arg_tree_b = arg_tree_aux
            elif (
                    tv_aux == TruthValue.TRUE and
                    (arg_tree_b == ArgTree() or self.stronger(arg_tree_b, arg_tree_aux) != arg_tree_b)
            ):
                tv_b = TruthValue.TRUE
                term_inst = InstantiatedTerm(agent, term_aux, term, sim)
                arg_tree_b = arg_tree_aux

        return term_inst, tv_b, arg_tree_b

    def similarity(self, term1, term2):
        return self.system.similarity(term1, term2)

    def stronger(self, arg_tree1, arg_tree2):

        rank_arg_tree1 = self.calculate_arg_tree_rank(arg_tree1)
        rank_arg_tree2 = self.calculate_arg_tree_rank(arg_tree2)

        if rank_arg_tree1 >= rank_arg_tree2:
            return arg_tree1
        #else
        return arg_tree2

    def calculate_arg_tree_rank(self, arg_tree: ArgTree):
        support_set = arg_tree.get_all_foreign_leaves()
        return sum([self.calculate_term_rank(term) for term in support_set])

    def calculate_term_rank(self, term: InstantiatedTerm):
        return self.preference_function(term.definer) * term.sim_degree

    def _key(self):
        return self.id

