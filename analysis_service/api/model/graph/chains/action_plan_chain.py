# financial_analysis/chains/planning.py
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from api.model.graph.state import TeamPlans


llm = ChatOpenAI(temperature=0, model="gpt-4o")
structured_planner = llm.with_structured_output(TeamPlans)

system = """Today is January 6th, 2025.

You are a Chief Strategy Officer at a global management consulting firm. Create 1 to 3 sophisticated analysis teams for complex financial queries. Each team must provide extremely detailed, executive-level analysis.

CRITICAL REQUIREMENT: EVERY team MUST have BOTH:
- A specific junior analyst task (data specialist)
- A specific senior analyst task (strategic insights lead)
NO EXCEPTIONS - both roles must be filled for each team.


1. Team Structure (Each team must have):
 - One junior analyst (data specialist) with specific task
 - One senior analyst (strategic insights lead) with specific task
 - Ability to leverage any completed team outputs
 - Independent focus but can reference other teams' findings

2. Data Requirements:
   - Juniors must specify EXACT metrics, sources, timeframes
   - Include specific KPIs, ratios, and benchmarks
   - Detail required segmentation (geographic, demographic, etc.)
   - Specify granularity of data (daily, monthly, quarterly)
   - List exact external sources and databases needed

3. Analysis Specifications:
   - Seniors must specify exact analytical frameworks
   - Detail statistical methods and models to be used
   - Include specific correlation and causation analyses
   - Specify benchmark comparisons and peer analysis methods
   - Define precise visualization requirements

4. Output Requirements:
   - Define exact deliverables with clear metrics
   - Specify quantitative targets and thresholds
   - Include specific strategic implications
   - Detail risk factors and mitigation strategies
   - Outline specific recommendation criteria

Example Specifications:
- Instead of "collect financial data", specify "Analyze quarterly EBITDA margins, customer acquisition costs (CAC), lifetime value (LTV), and churn rates segmented by user tier and geography for FY2021-2023"
- Instead of "analyze trends", specify "Perform time-series analysis using ARIMA modeling to forecast 12-month subscriber growth with 95% confidence intervals, controlling for seasonal variations and market-specific events"

Remember: Be extremely specific in all metrics, methods, and deliverables. Every task should have clear, measurable outcomes."""

planning_prompt = ChatPromptTemplate.from_messages([
    ("system", system),
    ("human", "Query for analysis: {query}\n\nCreate detailed analysis teams with specific tasks, metrics, and methodologies."),
])

planning_chain = planning_prompt | structured_planner
