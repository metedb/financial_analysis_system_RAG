from api.model.graph.agents.base import BaseAnalyst
from api.model.graph.state import TeamPlan, AnalysisState
from typing import Dict, Any
from api.model.graph.tools.python_tool_senior import senior_analysis_tool
from config.settings import Settings
settings = Settings()
from langchain_core.tools import Tool




template = """
                    Today is January 6th, 2025.
                    You are a {role} at a global management consulting firm.
                    Your specific task: {task}
                    The required data has been made available to you by your junior team member with appropriate dataset summaries.
                    You can find the datasets' paths in {available_data} with appropriate descriptions.
                    Expected output: {expected_output}

                    Available tools: {tools}
                    Tool Names: {tool_names} (use exactly one of these at each step)

                    **CRITICAL TOOL DESCRIPTIONS**
                    - python_repl': Use for advanced data analysis and visualisation using Python code.
                    - 'web_search': Use when you need additional insights to support your advanced analysis.

                    **CRITICAL PYTHON GUIDANCE**
                    If using the python_repl tool, you must write complete, executable Python code. Do not use placeholders.

                    **Reasoning format**:
                    - Question: {input}
                    - Thought: [Reflect on what is needed for the task and how to do it]
                    - Action: ONE of [{tool_names}]
                    - Action Input: input for the chosen action
                    - Observation: [Analyze and interpret the tool's response]
                    ... (above steps can repeat N times)
                    - Thought: I now know the final answer
                    - Final Answer: Advanced analysis with a very detailed and technical summary of your findings.

                    Notes:
                    1. Be concise and precise in your thoughts and actions.

                    Begin!
                    Question: {input}
                    Thought: {agent_scratchpad}
                    """



class SeniorAnalyst(BaseAnalyst):
    def __init__(self, team_plan: TeamPlan, model_config: dict, state):
        super().__init__(team_plan, model_config)
        self.task = team_plan.senior_task
        self.available_data = team_plan.shared_data
        self.expected_output = team_plan.senior_expected_output
        self.role = "Senior Financial Analyst"

        self.python_repl = senior_analysis_tool(state)
        self.state = state
       
        self.tools = [
            Tool(
                name="python_repl",
                description="""Python REPL for advanced data analysis, calculations, and visualisation. Input should be valid Python code. """,
                func=lambda x: self.python_repl.__call__(
                x, 
                state=self.state,
                team_plan=self.team_plan
    )
            )
        ]

        partial_variables={
                "role": self.role,
                "task": self.task,
                "available_data": str(self.available_data),
                "expected_output": str(self.expected_output)
            }
        prompt = self._create_prompt(template, partial_variables, self.tools)
        self._create_agent(prompt)




    def execute(self, input_query: str) -> Dict[str, Any]:
        result = super().execute(input_query, self.state)
        self.state.team_outputs[self.team_plan.id] = {
            "analysis": result.get("Final Answer", "")
        }
        return 
    

