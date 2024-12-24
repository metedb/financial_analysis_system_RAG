from typing import Dict
from api.model.graph.state import AnalysisState
from dataclasses import asdict
from api.model.graph.agents.base import BaseAnalyst
from api.model.graph.agents.senior import SeniorAnalyst

def execute_senior_analysis(state: AnalysisState) -> AnalysisState:
    """Node for executing senior analyst tasks"""
    current_team = state.teams[state.current_team_index]
    senior_analyst = SeniorAnalyst(
        team_config=current_team,
        model_config={
            "model": "gpt-3.5-turbo",
            "temperature": 0.0
        })
    
    senior_analyst.execute(
        input_query=state.query,
        analysis_state=state
    )
        
    return state
