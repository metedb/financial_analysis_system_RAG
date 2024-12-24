from api.model.graph.agents.base import BaseAnalyst
from api.model.graph.state import TeamConfig, AnalysisState
from typing import Dict, Any





template = """
                    Today is December 24th, 2024.
                    You are a {role} at a global management consulting firm.
                    Your specific task: {task}
                    The required data {data_needs} has been made available to you by your junior team member with appropriate dataset summaries. 
                    You can find the datasets in {available_data}.
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
    def __init__(self, team_config: TeamConfig, model_config: dict, state: AnalysisState):
        super().__init__(team_config, model_config)
        self.task = team_config.senior_task
        self.available_data = team_config.junior_datasets
        self.expected_output = team_config.senior_output
        self.role = "Senior Financial Analyst"

        partial_variables={
                "role": self.role,
                "task": self.task,
                "data_needs": str(self.data_needs),
                "available_data": self.team_config.junior_datasets,
                "expected_output": str(self.expected_output)
            }
        prompt = self._create_prompt(template, partial_variables, self.tools)
        self._create_agent(prompt)




    def execute(self, input_query: str, analysis_state: AnalysisState) -> Dict[str, Any]:
        result = super().execute(input_query, analysis_state)
        analysis_state.team_outputs[self.team_config.id] = {
            "analysis": result.get("Final Answer", "")
        }
        return 
    

