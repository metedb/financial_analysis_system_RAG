import os
import pandas as pd
import matplotlib as plt
from io import BytesIO
from langchain_experimental.utilities import PythonREPL

from api.model.graph.state import TeamPlan, AnalysisState


def load_dataset(file_path: str) -> pd.DataFrame:
    """Loads a DataFrame from a CSV file (if you need it directly in Python)."""
    return pd.read_csv(file_path)


class senior_analysis_tool:
    def __init__(self, state: AnalysisState):
        plt.use('Agg')
        self.python_repl = PythonREPL()
        self.state = state
        
        setup_code = """
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd   ###need to extend further!!
"""
        try:
            self.python_repl.run(setup_code)
        except Exception as e:
            print(f"Setup failed: {repr(e)}")

    def __call__(
        self,
        input_code: str,
        state: AnalysisState = None,
        team_plan: TeamPlan = None,
    ):
        """
        Executes Python code within this REPL context.
        
        1. Auto-load each file in team_plan.shared_data into the REPL:
           - If it's .csv, load as a DataFrame (dataset_1, dataset_2, ...)
        2. Execute the given code (input_code) in the REPL.
        3. Capture any new figures in state.shared_figures.
        """
        try:
            if team_plan:
                for idx, (desc, file_path) in enumerate(team_plan.shared_data.items(), start=1):
                    ext = os.path.splitext(file_path)[1].lower() 
                    if ext == ".csv":
                        var_name = f"dataset_{idx}"
                        load_code = (
                            f"import pandas as pd\n"
                            f"{var_name} = pd.read_csv(r'{file_path}')\n"
                            f'print("Loaded dataset for {desc} as {var_name}")'
                        )
                    else:
                        var_name = f"file_{idx}"
                        load_code = (
                            f"import os\n"
                            f"with open(r'{file_path}', 'rb') as f:\n"
                            f"    {var_name} = f.read()\n"
                            f'print("Loaded unknown file for {desc} as {var_name}")'
                        )

                    # run the load code in the REPL (need to carry this over to initialisation)
                    self.python_repl.run(load_code)

            result = self.python_repl.run(input_code)
            
            # capture any new figures
            if state and team_plan:
                for fig in [plt.figure(n) for n in plt.get_fignums()]:
                    buf = BytesIO()
                    fig.savefig(buf, format='png')
                    buf.seek(0)
                    state.shared_figures[
                        f"team_{self.state.current_team_index}_fig_{len(self.state.shared_figures)}"
                    ] = buf
                    plt.close(fig)
            
            return str(result)
        except Exception as e:
            return f"Execution failed: {repr(e)}"

