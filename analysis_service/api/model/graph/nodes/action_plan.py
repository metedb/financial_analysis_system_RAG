from api.model.graph.state import AnalysisState, TeamPlan
from api.model.graph.chains.action_plan_chain import planning_chain 

def plan_teams(state: AnalysisState) -> AnalysisState:
    """Node for planning team configurations"""
    result = planning_chain.invoke({"query": state.query})
    print("Team Plans:")
    
    team_configs = [
        TeamPlan(
            id=plan.id - 1,
            focus_area=plan.focus_area,
            expected_output=plan.expected_output,
            junior_task=plan.junior_task,
            junior_data_needs=plan.junior_data_needs,
            junior_expected_output=plan.junior_expected_output,
            senior_task=plan.senior_task,
            senior_expected_output=plan.senior_expected_output
        ) for plan in result.plans
    ]
    
    state.teams = team_configs
    
    for plan in state.teams:
        print(f"ID: {plan.id}")
        print(f" Focus Area: {plan.focus_area}")
        print(f" Expected Output: {plan.expected_output}")
        print(f" Junior Task: {plan.junior_task}")
        print(f" Junior Data Needs: {', '.join(plan.junior_data_needs)}")
        print(f" Junior Expected Output: {plan.junior_expected_output}")
        print(f" Senior Task: {plan.senior_task}")
        print(f" Senior Expected Output: {plan.senior_expected_output}")
        print("-" * 40)

    state.current_team_index = 0
    return state