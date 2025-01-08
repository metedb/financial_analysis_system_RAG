from api.model.graph.state import TeamPlan, AnalysisState
from langchain_experimental.utilities import PythonREPL
from typing import List, Dict, Any, Optional


import os
import tempfile
import pandas as pd

def store_data(data: Any, dataset_id: str) -> str:
    """
    Stores either a DataFrame (as CSV) or a text string (as .txt).
    Returns the file path.
    """
    file_path = ""
    if isinstance(data, pd.DataFrame):
        if data.empty:
            raise ValueError("Cannot store empty DataFrame")
        file_path = os.path.join(tempfile.gettempdir(), f"{dataset_id}.csv")
        data.to_csv(file_path, index=False)
    else:
        raise TypeError(f"Unsupported data type: {type(data)}. Must be DataFrame.")
    return file_path




class junior_analysis_tool:
    def __init__(self, state: AnalysisState):
        self.python_repl = PythonREPL()
        self.state = state
        
        setup_code = """
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd

        final_dataset = None
        final_dataset_description = None

        def mark_final_dataset(df, description):
            global final_dataset, final_dataset_description
            if not isinstance(df, pd.DataFrame):
                raise TypeError("Input must be a pandas DataFrame")
            final_dataset = df
            final_dataset_description = description
"""
        # we run this setup code once at initialization
        self.python_repl.run(setup_code)

    def __call__(self, input_code: str, team_plan: TeamPlan = None):
        try:
            result = self.python_repl.run(input_code)
            
            # check if a final dataset was marked
            if team_plan:
                final_df = self.python_repl.locals.get('final_dataset')
                df_desc = self.python_repl.locals.get('final_dataset_description')

                if final_df is not None and df_desc is not None:
                    file_path = store_data(final_df, f"team_{team_plan.id}_{df_desc}")
                    team_plan.shared_data[df_desc] = file_path

                    # reset them in the REPL in case the tool is used again
                    self.python_repl.run("final_dataset = None; final_dataset_description = None")

            return str(result)

        except Exception as e:
            return f"Execution failed: {repr(e)}"


 