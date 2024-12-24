from typing import Dict
from api.model.graph.state import AnalysisState
from dataclasses import asdict
from api.model.graph.agents.base import BaseAnalyst
from api.model.graph.agents.junior import JuniorAnalyst

def execute_junior_analysis(state: AnalysisState) -> AnalysisState:
    """Node for executing junior analyst tasks"""
    current_team = state.teams[state.current_team_index]
    junior_analyst = JuniorAnalyst(
        team_config=current_team,
        model_config={
            "model": "gpt-4",
            "temperature": 0.0
        }, state=state)

    junior_analyst.execute(
        input_query=state.query,
        analysis_state=state
    )   
     
    return state
