from api.model.graph.state import AnalysisState
from api.model.graph.agents.junior import JuniorAnalyst

def execute_junior_analysis(state: AnalysisState) -> AnalysisState:
    """Node for executing junior analyst tasks"""
    current_team = state.teams[state.current_team_index]
    junior_analyst = JuniorAnalyst(
        team_plan=current_team,
        model_config={
            "api_key": "YOUR_API_KEY_HERE",
            "model": "gpt-4o",
            "temperature": 0.0
        }, state=state)

    junior_analyst.execute(
        input_query=state.query
        )   
     
    return state
