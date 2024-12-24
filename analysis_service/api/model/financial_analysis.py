from dotenv import load_dotenv
from .graph.state import AnalysisState, TeamPlan
from .graph.nodes.action_plan import plan_teams
from .graph.nodes.check_hallucinations import grade_hallucination_node
from .graph.nodes.junior_analyst import execute_junior_analysis
from .graph.nodes.senior_analyst import execute_senior_analysis
from .graph.nodes.supervisor import execute_supervisor_review
from .graph.nodes.send_to_pdf import generate_pdf
from langgraph.graph import StateGraph, START, END
# from .graph.nodes.check_hallucinations import grade_hallucination_node
import asyncio



###fix the main flow here!!!

async def get_financial_analysis(query: str):
    load_dotenv()
    
    workflow = StateGraph(AnalysisState)
    ###correct logic here
    for team in teams:
        workflow.add_node("supervisor_review", execute_supervisor_review) 
        workflow.add_node("supervisor_review", execute_supervisor_review) 

    workflow.add_node("action_plan", plan_teams)
    workflow.add_node("supervisor_review", execute_supervisor_review) 
    workflow.add_node("send_to_pdf", generate_pdf)  
    workflow.add_edge("supervisor_review", "send_to_pdf")

    
    workflow.set_entry_point("action_plan")    
    
    workflow.add_conditional_edges(
        "senior_analysis",
        grade_hallucination_node,
        {
            "grounded": "supervisor_review",       
            "ungrounded": "senior_analysis",       
        }
    )
    
    workflow.add_edge("send_to_pdf", "complete")
    
    app = workflow.compile()

    app.get_graph().draw_mermaid_png(output_file_path="graph.png")
    
    print(f"Executing financial analysis for query: {query}")
    
    stream = app.stream({"query": query}, subgraphs=True)
    
    results = await asyncio.to_thread(list, stream)
    
    # Process results
    for state in results:
        print(state)
        print("----")


query = "Analyze AAPL's last quarter performance and create a visualization comparing revenue and profit margins"

asyncio.run(get_financial_analysis(query))