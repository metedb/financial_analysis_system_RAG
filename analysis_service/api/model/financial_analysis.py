from dotenv import load_dotenv
from api.model.graph.state import AnalysisState
from api.model.graph.nodes.action_plan import plan_teams
from api.model.graph.nodes.supervisor import execute_supervisor_review
from api.model.graph.nodes.send_to_pdf import generate_pdf
from api.model.graph.nodes.execute_tasks import execute_tasks

from langgraph.graph import StateGraph, START, END
# from .graph.nodes.check_hallucinations import grade_hallucination_node
import asyncio


def check_teams(state: AnalysisState) -> AnalysisState:
    index = state.current_team_index

    if index < len(state.teams):
        return "NEXT TEAM"
    
    else: return "SUPERVISOR"




async def get_financial_analysis(query: str):
    load_dotenv("/Users/metedibi/Desktop/LLM_STUDIES/financial_rag/analysis_service/.env")
    
    workflow = StateGraph(AnalysisState)


    workflow.add_node("action_plan", plan_teams)
    workflow.add_node("execute_tasks", execute_tasks)
    workflow.add_node("supervisor_review", execute_supervisor_review) 
    workflow.add_node("send_to_pdf", generate_pdf)  

    
    workflow.set_entry_point("action_plan")    
    
    workflow.add_edge("action_plan", "execute_tasks")
    workflow.add_edge("supervisor_review", "send_to_pdf")
    workflow.add_edge("send_to_pdf", END)

    workflow.add_conditional_edges(
        "execute_tasks",
        check_teams,
        {
            "NEXT TEAM": "execute_tasks",
            "SUPERVISOR": "supervisor_review",
        },
    )
    
    
    app = workflow.compile()

    app.get_graph().draw_mermaid_png(output_file_path="graph.png")

    print(f"Executing financial analysis for query: {query}")
    
    stream = app.stream({"query": query}, subgraphs=True)
    
    results = await asyncio.to_thread(list, stream)
    
    for state in results:
        print(state)
        print("----")

query = "Today is January 6th, 2025. I need a forecast comparison of both Apple and Microsoft stock for next week, purely based on previous year's stock movements."

asyncio.run(get_financial_analysis(query))