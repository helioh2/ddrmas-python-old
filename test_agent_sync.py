from agent_sync_arguments import MultiAgentSystem, Agent, Literal, Term
from builders import Builder
from mushroom_rules_examples import R_MUSHROOM, R_FOCUS_MUSHROOM


def create_scenario_mushroom_hunters():

    def similarity_function(term1, term2):
        if "amanita_velosa" in (term1, term2) and "springtime_amanita" in (term1, term2):
            return 0.8
        if "amanita" in (term1, term2) and "springtime_amanita" in (term1, term2):
            return 0.5
        if "amanita" in (term1, term2) and "amanita_velosa" in (term1, term2):
            return 0.5
        return term1.literal == term2.literal

    system = MultiAgentSystem(similarity_function, 0.4)

    agents_dict = dict(
        A=Agent("A", system),
        B=Agent("B", system),
        C=Agent("C", system),
        D=Agent("D", system),
        E=Agent("E", system),
    )

    builder = Builder(agents_dict)

    for id_, rules in R_MUSHROOM.items():
        agents_dict[id_].rules = builder.build_rules(rules)

    agents_dict["A"].preference_function["B"] = 0.4
    agents_dict["A"].preference_function["C"] = 0.6
    agents_dict["A"].preference_function["D"] = 0.2
    agents_dict["A"].preference_function["E"] = 0.8

    agents_dict["B"].preference_function["A"] = 0.5
    agents_dict["B"].preference_function["C"] = 0.5
    agents_dict["B"].preference_function["D"] = 0.5
    agents_dict["B"].preference_function["E"] = 0.5

    agents_dict["C"].preference_function["A"] = 0.8
    agents_dict["C"].preference_function["B"] = 0.4
    agents_dict["C"].preference_function["D"] = 0.4
    agents_dict["C"].preference_function["E"] = 0.8

    agents_dict["D"].preference_function["A"] = 0.4
    agents_dict["D"].preference_function["B"] = 0.4
    agents_dict["D"].preference_function["C"] = 0.8
    agents_dict["D"].preference_function["E"] = 0.8

    agents_dict["E"].preference_function["A"] = 0.4
    agents_dict["E"].preference_function["B"] = 0.6
    agents_dict["E"].preference_function["C"] = 0.2
    agents_dict["E"].preference_function["D"] = 0.8

    system.agents = agents_dict

    return system


def test_scenario_mushroon_hunters():
    system = create_scenario_mushroom_hunters()
    term_to_query = Term(system.agents["A"], Literal("col(m1)"))

    builder = Builder({})
    focus_knowledge_base = builder.build_rules(R_FOCUS_MUSHROOM)

    answer = system.agents["A"].initialize_query(term_to_query, focus_knowledge_base)


test_scenario_mushroon_hunters()