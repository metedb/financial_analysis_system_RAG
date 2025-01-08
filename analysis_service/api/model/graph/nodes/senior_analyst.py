from typing import Dict
from api.model.graph.state import AnalysisState
from api.model.graph.agents.senior import SeniorAnalyst

def execute_senior_analysis(state: AnalysisState) -> AnalysisState:
    """Node for executing senior analyst tasks"""
    current_team = state.teams[state.current_team_index]
    senior_analyst = SeniorAnalyst(
        team_plan=current_team,
        model_config={
            "api_key": "YOUR_API_KEY_HERE",
            "model": "gpt-4",
            "temperature": 0.0
        }, state=state)
 
    senior_analyst.execute(
        input_query=state.query
        )
        
    return state
