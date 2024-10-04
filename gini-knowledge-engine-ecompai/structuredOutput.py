from pydantic import BaseModel
import streamlit as st
import openai
from utils.prompt_loader import load_prompt
from utils.query_executor import execute_query
from config.db_config import DB_CONFIG
from openai import OpenAI
import pandas as pd
client = OpenAI(
    api_key ='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'
)

# Set up your OpenAI API key
#openai.api_key = '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'

class QueryOutput(BaseModel):
    query: str
    queryDescription: str

def create_sql_query(natural_language_input: str, prompt_filename: str) -> str:
    """
    Generates an SQL query from natural language input using OpenAI's API.

    Args:
        natural_language_input (str): The natural language description of the query.
        prompt_filename (str): The path to the prompt text file.

    Returns:
        str: The generated SQL query.
    """
    try:
        system_prompt = load_prompt(prompt_filename)
        user_message = f"{system_prompt}\n\nNatural language input: {natural_language_input}"

        response = client.beta.chat.completions.parse(
            # model="gpt-4o-mini",
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format=QueryOutput,
        )

        print('response', response)
    
        sql_query = response.choices[0].message.parsed
        print('sql_query response', sql_query)
        
        return sql_query
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    st.title("SQL Query Generator from Natural Language")

    natural_language_input = st.text_area("Enter your query:")
    
    if st.button("Generate SQL Query"):
        if natural_language_input:
            sql_query = create_sql_query(natural_language_input, 'sql_prompt.txt')
            print('sql_query', sql_query)
            st.subheader("Generated SQL Query")
            st.code(sql_query, language='sql')

            st.subheader("Query Results")
            result = execute_query(sql_query.query, DB_CONFIG)
            if result.status == "success":
                st.write(result.data)
                # df = pd.DataFrame(my_list_of_lists, columns=['ID', 'Name', 'Age'])
                df = pd.DataFrame(result)
                st.bar_chart(data=df)
            else:
                st.error(result.error)
        else:
            st.warning("Please enter a query.")

if __name__ == "__main__":
    main()
