from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.agents.agent import AgentExecutor
from api.model.graph.state import TeamPlan, AnalysisState
from langchain_openai import ChatOpenAI

from config.settings import Settings

settings = Settings()

    

class BaseAnalyst:
    """Base class for analyst agents that handles common functionalities."""

    def __init__(
        self,
        team_plan: TeamPlan,
        model_config: dict):

        self.team_plan = team_plan
        self.llm = ChatOpenAI(**model_config)
        self.agent_executor = None
        self.tools = None



    def _create_prompt(self, template, partial_variables, tools) -> PromptTemplate:
        """Create the prompt template for the agent"""
        tool_names = [tool.name for tool in tools]
        tool_strings = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])

        partial_variables["tools"] = tool_strings
        partial_variables["tool_names"] = ", ".join(tool_names)        
        
        return PromptTemplate.from_template(
            template=template,
            partial_variables = partial_variables
        )
    

    def _create_agent(self, prompt):
        """Create the React agent with executor"""
        agent = create_react_agent(
            llm=self.llm, 
            tools=self.tools, 
            prompt=prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=20,
            return_intermediate_steps=True
        )


    def execute(self, input_query: str, analysis_state: AnalysisState) -> Dict[str, Any]:
        """
        Execute the agent. 
        We include analysis_state here so the child class signature matches.
        """
        result = self.agent_executor.invoke({
            "input": input_query,
            "analysis_state": analysis_state
        })
        return result
    

