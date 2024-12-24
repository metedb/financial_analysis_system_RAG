import httpx  
import pandas as pd 
from typing import List, Optional
import pandas as pd
import httpx
from langchain.tools.base import BaseTool
from langchain.base_language import BaseLanguageModel

from langchain_community.utilities.sql_database import SQLDatabase
from langchain.sql_database import SQLDatabase
from langchain_core.tools import BaseTool
from langchain_community.agent_toolkits.sql.toolkit import InfoSQLDatabaseTool, ListSQLDatabaseTool, QuerySQLCheckerTool
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool


"""Customised Descriptions for the SQL Toolkit utilised by agents."""
QUERY_TOOL_DESCRIPTION = """Input to this tool is a detailed and correct SQL query, output is a JSON-formatted result from the database.
        CRITICAL GUIDELINES:
        - Double quote ALL column names: "Column_Name"
        - Only use SELECT statements
        - Avoid LIMIT statements
        - Only query necessary columns, never use SELECT *
        - Break complex calculations into simpler steps
        If you get an error, verify schema and rewrite query."""

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
        self._ignore_tables = None
        self._include_tables = []
        self._all_tables = []
        self._metadata = None
        
    def get_tables(self) -> List[str]:
        """Get list of tables using SQL query"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        """
        result = self.run(query)
        return result['table_name'].tolist() if not result.empty else []

    def get_table_info(self, table_names: Optional[List[str]] = None) -> str:
        """Get table schema using SQL query"""
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
        return result.to_json(orient='records') if not result.empty else "[]"

    def run(self, query: str, *args, **kwargs) -> pd.DataFrame:
        """Execute SQL queries via HTTP endpoint"""
        with httpx.Client() as client:
            request_params = {"query": query}
            if kwargs.get('parameters'):
                request_params["parameters"] = kwargs['parameters']
                
            try:
                response = client.get(
                    self.endpoint_url,
                    params=request_params,
                    timeout=30.0
                )
                data = response.json()
                if "results" in data:
                    return pd.DataFrame(data["results"])
                return pd.DataFrame([{"message": data.get("message", "Query executed successfully")}])
            except Exception as e:
                return pd.DataFrame([{"error": str(e)}])
    

def create_enhanced_sql_toolkit(endpoint_url: str, llm: BaseLanguageModel) -> List[BaseTool]:
    db = HTTPSQLDatabase(endpoint_url)
    
    def json_formatter(result: pd.DataFrame) -> str:
        return result.to_json(orient='records')
    
    tool_configs = {
        QuerySQLDataBaseTool: {
            'description': QUERY_TOOL_DESCRIPTION,
            'formatter': json_formatter
        },
        InfoSQLDatabaseTool: {
            'description': INFO_TOOL_DESCRIPTION,
            'formatter': json_formatter
        },
        ListSQLDatabaseTool: {
            'description': LIST_TABLES_DESCRIPTION,
            'formatter': json_formatter
        },
        QuerySQLCheckerTool: {'description': CHECKER_TOOL_DESCRIPTION}
    }
    
    enhanced_tools = []
    
    for tool_class, config in tool_configs.items():
        kwargs = {
            'db': db,
            'llm': llm,
            'description': config['description']
        }
        
        if 'formatter' in config:
            kwargs['output_formatter'] = config['formatter']
            
        tool = tool_class(**kwargs)
        enhanced_tools.append(tool)
    
    return enhanced_tools