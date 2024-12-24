from api.model.graph.agents.base import BaseAnalyst
from api.model.graph.state import TeamConfig, AnalysisState
from typing import Dict, Any

JUNIOR_ANALYST_TEMPLATE = """Today is December 24th, 2024.
You are a {role} at a global management consulting firm.

TASK INFORMATION
---------------
Your specific task: {task}
Required data: {data_needs}
Expected output: {expected_output}

TOOLS
-----
You have access to the following tools:

{tools}

IMPORTANT NOTES
--------------
1. For historical data (stock prices, financial statements, metrics), ALWAYS use sql_tools first
2. Only use web_search for very recent market updates or news
3. When using python_repl:
   - Write complete, executable Python code
   - Use mark_final_dataset(df, "description") to store your final processed dataset
   - Always include proper error handling
   - Format numbers and dates appropriately


ALWAYS USE THE FOLLOWING FORMAT:
---------------------------------
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""

class JuniorAnalyst(BaseAnalyst):
    """Junior Financial Analyst agent responsible for data collection and organization."""
    
    def __init__(self, team_config: TeamConfig, model_config: dict,  state: AnalysisState ):
        super().__init__(team_config, model_config, state)
        
        self.task = team_config.junior_task
        self.data_needs = team_config.junior_data_needs
        self.expected_output = team_config.junior_expected_output
        self.role = "Junior Financial Analyst"

        prompt = self._create_prompt(
            template=JUNIOR_ANALYST_TEMPLATE,
            partial_variables={
                "role": self.role,
                "task": self.task,
                "data_needs": str(self.data_needs),
                "expected_output": str(self.expected_output)
            }
        )
        
        self._create_agent(prompt)

    def execute(self, input_query: str, analysis_state: AnalysisState) -> Dict[str, Any]:
        """Execute the junior analyst's task using parent's execution method."""
        return super().execute(input_query, analysis_state)
    




