from pydantic import BaseModel, Field
from typing import Optional, List
import mysql.connector
from mysql.connector import Error

class QueryResult(BaseModel):
    query: str
    data: Optional[List[dict]] = Field(default=None, description="The data retrieved from the database.")
    status: str
    error: Optional[str] = None

def execute_query(sql_query: str, db_config: dict) -> QueryResult:
    """
    Executes an SQL query against a MySQL database and retrieves data.

    Args:
        sql_query (str): The SQL query to execute.
        db_config (dict): Database configuration including host, database, user, and password.

    Returns:
        QueryResult: A structured output containing the query result and metadata.
    """
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql_query)
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        # Return the data as a structured output
        result = QueryResult(
            query=sql_query,
            data=data,
            status="success"
        )

    except Error as e:
        # Handle errors and return failure status
        result = QueryResult(
            query=sql_query,
            status="failure",
            error=str(e)
        )

    return result
