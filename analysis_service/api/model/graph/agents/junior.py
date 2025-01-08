from api.model.graph.agents.base import BaseAnalyst
from api.model.graph.state import TeamPlan, AnalysisState
from typing import Dict, Any
from api.model.graph.tools.python_tool_junior import junior_analysis_tool
from api.model.graph.tools.sql_tool import create_enhanced_sql_toolkit
from api.model.graph.tools.semantic_search_tool import create_news_search_tool
from config.settings import Settings
settings = Settings()
from langchain_core.tools import Tool


JUNIOR_ANALYST_TEMPLATE = """Today is January 6th, 2025.
You are a {role} at a global management consulting firm.

TASK INFORMATION
---------------
Your specific task: {task}
Required data: {data_needs}
Expected output: {expected_output}

ONLY STICK TO YOUR TASK AND EXPECTED OUTPUT. DISREGARD THE ORIGINAL USER QUERY.

TOOLS
-----
You have access to the following tools:

{tools}

--------------
IMPORTANT NOTES ON TOOL USAGE
1. NUMERICAL DATA:
   1.1 For historical data (stock prices, financial statements, metrics), ALWAYS use sql_tools first
   1.2 The sql_db_query should return a message including a “SQL Results saved to: /tmp/sql_results_xxxx.csv”
       - You MUST parse that file path to the python tool later when manipulating data
   1.3 After collecting data from sql_tools, ALWAYS USE THE "python_repl" tool to:
       - Load the CSV file with `df = pd.read_csv("<the_path_from_sql_results>")`
       - Manipulate or analyze df
       - If you want to store the final dataset for others, use `mark_final_dataset(df, 'some_description')`
---------------


ALWAYS USE THE FOLLOWING FORMAT:
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

JUNIOR_ANALYST_PYTHON_DESCRIPTION="""
Python REPL for data analysis and calculations. Input should be valid Python code.
IMPORTANT when working with SQL results:
  1. Parse the CSV file path from the sql_tools output (e.g. '/tmp/sql_results_xxxx.csv').
  2. Load the data by:
       df = pd.read_csv("/tmp/sql_results_xxxx.csv")
  3. Use mark_final_dataset(df, 'short_description') to store your final DataFrame in team_plan.shared_data.
"""


        
class JuniorAnalyst(BaseAnalyst):
    """Junior Financial Analyst agent responsible for data collection and organization."""
    
    def __init__(self, team_plan: TeamPlan, model_config: dict,  state: AnalysisState):
        super().__init__(team_plan, model_config)
        
        self.task = team_plan.junior_task
        self.data_needs = team_plan.junior_data_needs
        self.expected_output = team_plan.junior_expected_output
        self.role = "Junior Financial Analyst"

        self.python_repl = junior_analysis_tool(state)
        self.news_tool = create_news_search_tool(f"{settings.GATEWAY_URI}/news/search")
       
        self.sql_tools = create_enhanced_sql_toolkit(
            endpoint_url=f"{settings.GATEWAY_URI}/sql/search",
            llm=self.llm
        )       
        self.state = state
       
        self.tools = [
            *self.sql_tools,  

            Tool(
                name="python_repl",
                description= JUNIOR_ANALYST_PYTHON_DESCRIPTION,
                func=lambda x: self.python_repl.__call__(
                x, 
                team_plan=self.team_plan
    )
           ),

           self.news_tool
        ]


        prompt = self._create_prompt(
            template=JUNIOR_ANALYST_TEMPLATE,
            partial_variables={
                "role": self.role,
                "task": self.task,
                "data_needs": str(self.data_needs),
                "expected_output": str(self.expected_output)
            },
            tools=self.tools
        )
        
        self._create_agent(prompt)

    def execute(self, input_query: str) -> Dict[str, Any]:
        """Execute the junior analyst's task using parent's execution method."""
        return super().execute(input_query, self.state)
    




