from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain.agents.agent import AgentExecutor
from api.model.graph.state import TeamConfig, AnalysisState
from langchain_openai import ChatOpenAI
from api.model.graph.tools.python_REPL_tool import FinancialAnalysisREPL
from langchain_core.tools import Tool
from langchain.tools import TavilySearchResults
from api.model.graph.tools.sql_tool import create_enhanced_sql_toolkit
from config.settings import Settings

settings = Settings()

    

class BaseAnalyst:
    """Base class for analyst agents that handles common functionalities."""

    def __init__(
        self,
        team_config: TeamConfig,
        model_config: dict,
        state: AnalysisState
    ):
        self.team_config = team_config
        self.llm = ChatOpenAI(**model_config)
        self.web_search_tool = TavilySearchResults(max_results=5)
        self.python_repl = FinancialAnalysisREPL(state)
        self.sql_tools = create_enhanced_sql_toolkit(
            endpoint_url=f"{settings.GATEWAY_URI}/sql/search",
            llm=self.llm
        )       

        self.state = state
       
        self.tools = [
            *self.sql_tools,  

            Tool(
                name="python_repl",
                description="Python REPL for data analysis, calculations, and creating visualizations. Input should be valid Python code.",
                func=lambda x: self.python_repl.__call__(
                x, 
                state=self.state,  
                team_config=self.team_config
    )
            ),
            Tool(
                name="web_search",
                description="Search the web ONLY for recent news and real-time market updates. For historical data (stock prices, financial statements, metrics), use SQL tools first.",  # Modified to be explicit
                func=self.web_search_tool.invoke
            )
        ]

        self.agent_executor = None



    def _create_prompt(self, template, partial_variables) -> PromptTemplate:
        """Create the prompt template for the agent"""
        tool_names = [tool.name for tool in self.tools]
        tool_strings = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])

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
            max_iterations=5,
            return_intermediate_steps=True
        )


    def execute(self, input_query: str, analysis_state: AnalysisState) -> Dict[str, Any]:
        result = self.agent_executor.invoke({
            "input": input_query,
            "analysis_state": analysis_state
        })
        return result
    

