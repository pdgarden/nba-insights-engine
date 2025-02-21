"""Functions to choose how to display the result of a query."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports

import pandas as pd

from app.llm import query_llm

# -------------------------------------------------------------------------------------------------------------------- #
# Functions


def generate_question_response_md(question: str, result: pd.DataFrame) -> str:
    """Generate a markdown summary of a question based on its result."""

    prompt = f"""
You are an expert in NBA statistics. Someone asked you this question:
{question}

You generated a SQL query on a database with NBA data in order to respond to the question.
The result of the query is the following table:

{result.to_markdown(index=False)}

Write a summary of the result in markdown format.

Be concise. Do not write the question again. Do not write the SQL query. Do not write the table.
"""
    return query_llm(prompt=prompt, model_kind="light")
