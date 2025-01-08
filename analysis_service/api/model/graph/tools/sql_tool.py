import httpx  
import pandas as pd 
from typing import List, Optional, Dict, Any
import pandas as pd
import httpx
from langchain.tools.base import BaseTool
from langchain.base_language import BaseLanguageModel
import json
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import BaseTool
from langchain_community.agent_toolkits.sql.toolkit import InfoSQLDatabaseTool, ListSQLDatabaseTool, QuerySQLCheckerTool
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
import os
import tempfile

"""Customised Descriptions for the SQL Toolkit utilised by agents."""
QUERY_TOOL_DESCRIPTION = """Input to this tool is a detailed and correct SQL query, output is a JSON-formatted result from the database.
        CRITICAL GUIDELINES:
        - Double quote ALL column names: "Column_Name"
        - Only use SELECT statements
        - Avoid LIMIT statements
        - Only query necessary columns, never use SELECT *
        - Break complex calculations into simpler steps
        - If you get an error, verify schema and rewrite query.
        
        The results will be automatically saved as a CSV file and you'll get the file path.
        You can later load this CSV in python_repl using:
        df = pd.read_csv('the_file_path_you_received')
"""


LIST_TABLES_DESCRIPTION = """Use this tool FIRST before any other SQL operation.
        Returns all available tables in the database.
        You must check available tables before querying any table."""

INFO_TOOL_DESCRIPTION = """Input: comma-separated list of tables
        Output: Returns schema and sample rows for those tables in JSON format.
        CRITICAL:
        - Must be used after list_tables to confirm table existence
        - Use this to verify column names and data types before writing queries
        Example Input: table1, table2, table3"""

CHECKER_TOOL_DESCRIPTION = """ALWAYS use this tool before executing any query with sql_db_query!
        Validates SQL query for:
        - Correct column names and quotes
        - Proper date handling
        - Join conditions
        - Data type matching
        - SQL syntax"""



class HTTPSQLDatabase(SQLDatabase):
    """Custom SQL Database that works over HTTP."""
    
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        self._engine = None
        self._schema = None
        
        # change these to sets instead of None or lists:
        self._ignore_tables = set()
        self._include_tables = set()
        self._all_tables = set()  # will populate in get_tables()
        
        self._metadata = None

    @property
    def dialect(self) -> str:
        return "postgresql"

    def get_tables(self) -> List[str]:
        """Get list of tables using SQL query."""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        """
        result = self.run(query)
        #extract table names from JSON structure
        table_list = [row['table_name'] for row in result]
        self._all_tables = set(table_list)
        return table_list

    def get_usable_table_names(self) -> List[str]:
        """
        Return the difference of _all_tables and _ignore_tables in sorted order.
        Called by some SQL tools to figure out which tables can be queried.
        """
        if not self._all_tables:
            self.get_tables()
        return sorted(self._all_tables - self._ignore_tables)

    def get_table_info(self, table_names: Optional[List[str]] = None) -> str:
        """Get table schema using SQL query."""
        if not table_names:
            return "No tables specified"
        
        query = """
        SELECT 
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_name IN ({})
        AND table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """.format(','.join(f"'{name}'" for name in table_names))
        
        result = self.run(query)
        return json.dumps(result)
    
    def save_sql_results(self, results: List[Dict[str, Any]], query_hash: str) -> str:
        """
        Save SQL results (list of row dicts) to disk and return the file path.
        """
        file_path = os.path.join(tempfile.gettempdir(), f"sql_results_{query_hash}.csv")
        df = pd.DataFrame(results)
        df.to_csv(file_path, index=False)
        return file_path


    def enhanced_sql_formatter(self, results: List[Dict[str, Any]]) -> str:
        """
        1. Save the list of row dicts as a CSV file.
        2. Return a short text with the file path and a small preview.
        """
        if not results:
            return "Query returned no results"

        # create a unique hash from results for the file name
        import hashlib
        content_hash = hashlib.md5(str(results).encode()).hexdigest()[:8]

        # save to disk
        file_path = self.save_sql_results(results, content_hash)

        # return a small preview
        df = pd.DataFrame(results)
        preview_df = df.head()  # first few rows
        return (
        f"SQL Results saved to: {file_path}\n"
        f"<<CSV_FILE_PATH:{file_path}>>\n"   # <-- ADDED MARKER
        f"Preview:\n{preview_df.to_string(index=False)}\n\n"
        f"Shape: {df.shape}\n"
        f"Columns: {', '.join(df.columns)}"
    )


    def run(self, query: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Execute SQL queries via HTTP endpoint, return rows as a list of dicts:
        [ {"col1": val1, "col2": val2}, ... ].
        """
        with httpx.Client() as client:
            request_params = {"query": query}
            if 'parameters' in kwargs:
                request_params["parameters"] = kwargs['parameters']

            try:
                response = client.get(
                    self.endpoint_url,
                    params=request_params,
                    timeout=30.0
                )
                data = response.json()
                
                results = data.get("results", [])
                
                if not results:
                    return []

                return results

            except Exception as e:
                return [{"error": str(e)}]
            

class StrictQuerySQLDataBaseTool(QuerySQLDataBaseTool):
    def _call(self, inputs: str) -> str:
        """Override to ensure we only return the final formatted text."""
        query = inputs.strip()
        results = self.db.run(query)

        if self.output_formatter:
            final_text = self.output_formatter(results)
        else:
            final_text = str(results)
        
        return final_text

    

def create_enhanced_sql_toolkit(endpoint_url: str, llm: BaseLanguageModel) -> List[BaseTool]:
    db = HTTPSQLDatabase(endpoint_url)
    
    def json_formatter(result: dict) -> str:
        """Simple JSON formatter that doesn't need conversion"""
        return json.dumps(result)
    
    tool_configs = {
        StrictQuerySQLDataBaseTool: {
            'name': 'sql_db_query',  
            'description': QUERY_TOOL_DESCRIPTION,
            'formatter': db.enhanced_sql_formatter
            #'verbose': False
            # 'return_direct': True
        },
        InfoSQLDatabaseTool: {
            'name': 'sql_db_schema',
            'description': INFO_TOOL_DESCRIPTION,
            'formatter': json_formatter
        },
        ListSQLDatabaseTool: {
            'name': 'sql_db_list_tables',
            'description': LIST_TABLES_DESCRIPTION,
            'formatter': json_formatter
        },
        QuerySQLCheckerTool: {
            'name': 'sql_db_query_checker',
            'description': CHECKER_TOOL_DESCRIPTION}
    }
    
    enhanced_tools = []
    
    for tool_class, config in tool_configs.items():
        kwargs = {
            'db': db,
            'llm': llm,
            'name': config['name'], 
            'description': config['description']
        }
        
        if 'formatter' in config:
            kwargs['output_formatter'] = config['formatter']

        # if 'verbose' in config:
        #     kwargs['verbose'] = config['verbose']
        # if 'return_direct' in config:
        #     kwargs['return_direct'] = config['return_direct']
            
        tool = tool_class(**kwargs)
        enhanced_tools.append(tool)
    
    return enhanced_tools