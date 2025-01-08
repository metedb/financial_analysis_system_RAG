from typing import List, Dict
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from io import BytesIO


class TeamPlan(BaseModel):
    """Structure for a team's configuration"""
    id: int = Field(description="Team identifier")
    focus_area: str = Field(description="Team's main focus area for analysis")
    expected_output: str = Field(description="Detailed description of expected team output")
    junior_task: str = Field(description="Specific task for junior analyst")
    junior_data_needs: List[str] = Field(description="Specific data that needs to be collected by junior analyst")
    junior_expected_output: str = Field(description="Expected output format for junior analyst")
    senior_task: str = Field(description="Specific task for senior analyst")
    senior_expected_output: str = Field(description="Expected output format from the senior analyst")
    shared_data: Dict[str, str] = Field(description= "Organised dataset from the junior to be used by the senior",default_factory=dict)  
    output: str = Field(description= "The actual output of the team", default_factory=str)



    class Config:
        arbitrary_types_allowed = True

class TeamPlans(BaseModel):
    """Wrapper for multiple team plans"""
    plans: List[TeamPlan] = Field(
        description="List of team plans for the analysis",
        default_factory=list
    )

    class Config:
        arbitrary_types_allowed = True


@dataclass
class AnalysisState:
    """Maintains the state of the financial analysis workflow"""
    query: str  ###user query
    teams: List[TeamPlan] = field(default_factory=list)   ###list of teams along with their own action plans
    current_team_index: int = 0  ###which team is currently working on the task
    team_outputs: Dict[int, str] = field(default_factory=dict)  # stores output of each team, contains the final analysis by the senior
    shared_figures: Dict[str, BytesIO] = field(default_factory=dict) ## stores plots of each team

