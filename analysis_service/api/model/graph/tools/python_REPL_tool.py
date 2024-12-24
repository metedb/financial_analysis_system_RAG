from api.model.graph.state import TeamConfig, AnalysisState
from langchain_experimental.utilities import PythonREPL
import matplotlib as plt
from io import BytesIO

class FinancialAnalysisREPL:
    def __init__(self, state: AnalysisState):
        # plt.use('Agg') 
        self.python_repl = PythonREPL()
        self.state = state
        
        setup_code = """
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        
        # Your existing setup code...
        
        # Add a global to track final dataset
        final_dataset = None
        final_dataset_description = None
        
        def mark_final_dataset(df, description):
            '''Helper function to mark a dataset as final'''
            global final_dataset, final_dataset_description
            final_dataset = df
            final_dataset_description = description
        """
        try:
            self.python_repl.run(setup_code)
        except Exception as e:
            print(f"Setup failed: {repr(e)}")

    def __call__(self, input_code: str, state: AnalysisState = None, team_config: TeamConfig = None):
        try:
            result = self.python_repl.run(input_code)
            
            if state and team_config:
                for fig in [plt.figure(n) for n in plt.get_fignums()]:
                    buf = BytesIO()
                    fig.savefig(buf, format='png')
                    buf.seek(0)
                    state.shared_figures[f"team_{self.state.current_team_index}_fig_{len(self.state.shared_figures)}"] = buf
                    plt.close(fig)
                
                final_df = self.python_repl.locals.get('final_dataset')
                description = self.python_repl.locals.get('final_dataset_description')
                
                if final_df is not None and description is not None:
                    if team_config.id not in team_config.junior_datasets:
                        team_config.junior_datasets[team_config.id] = {}
                    
                    team_config.junior_datasets[team_config.id][description] = final_df
                    
                    self.python_repl.run("final_dataset = None; final_dataset_description = None")
            
            return str(result)
        except Exception as e:
            return f"Execution failed: {repr(e)}"
 