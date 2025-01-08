from api.model.graph.state import AnalysisState
from api.model.graph.chains.check_hallucinations_chain import hallucination_grader
from api.model.graph.nodes.junior_analyst import execute_junior_analysis
from api.model.graph.nodes.senior_analyst import execute_senior_analysis
from langgraph.graph import StateGraph, END



# def load_csv_as_text(file_path: str) -> str:
#     """
#     Loads the CSV and returns a string representation.
#     For large CSVs, you might want to summarize or chunk.
#     """
#     import pandas as pd
#     df = pd.read_csv(file_path)
#     # Convert to a string. For small CSVs, df.to_csv() is easy.
#     # For bigger data, you might want a subset or summary.
#     return df.to_csv(index=False)

# def grade_generation_grounded_in_documents_and_question(state: AnalysisState) -> str:
#     print("---CHECK HALLUCINATIONS---")
#     index = state.current_team_index
#     team_state = state.teams[index]

#     # 'team_state.shared_data' is { 'description': 'path/to.csv', ... }
#     # We'll load each CSV, convert to text, and combine them.
#     loaded_texts = []
#     for desc, file_path in team_state.shared_data.items():
#         csv_text = load_csv_as_text(file_path)
#         # We'll label it so the grader sees which dataset it's from
#         labeled_text = f"Dataset Description: {desc}\n\n{csv_text}"
#         loaded_texts.append(labeled_text)

#     # Combine all the text into one big string:
#     documents_text = "\n\n".join(loaded_texts)

#     # Now retrieve the final Senior output from 'state.team_outputs'
#     output_text = state.team_outputs[index]

#     # Pass them into the grader:
#     score = hallucination_grader.invoke({"documents": documents_text, "output": output_text})

#     # If the grader’s binary_score is True → "grounded"
#     if score.binary_score:
#         print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
#         return "OK"
#     else:
#         print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
#         return "HALLUCINATION"



def execute_tasks(state: AnalysisState) -> AnalysisState:    
    team_workflow = StateGraph(AnalysisState)
    
    team_workflow.add_node("junior_analysis", execute_junior_analysis)
    team_workflow.add_node("senior_analysis", execute_senior_analysis)
    team_workflow.set_entry_point("junior_analysis")    

    team_workflow.add_edge("junior_analysis", "senior_analysis")
    team_workflow.add_edge("senior_analysis", END)


    # team_workflow.add_conditional_edges(
    #     "senior_analysis",
    #     grade_generation_grounded_in_documents_and_question,
    #     {
    #         "HALLUCINATION": "senior_analysis",
    #         "OK": END,
    #     },
    # )
    
    sub_app = team_workflow.compile()

    sub_app.get_graph().draw_mermaid_png(output_file_path="graph_sub.png")

    stream = sub_app.stream(state)
    all_states = list(stream)  

    final_sub_state = all_states[-1] 

    final_sub_state.current_team_index += 1

    return state


    
