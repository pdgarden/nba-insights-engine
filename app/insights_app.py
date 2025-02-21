"""Streamlit app to take a user question and return an answer by generating a SQL query executed on the database."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports

import streamlit as st

from app.db.dao import sql_to_df
from app.logic.ner_retrieval import replace_names_in_text
from app.logic.question_to_sql import generate_sql_query
from app.logic.results_display import generate_question_response_md

# -------------------------------------------------------------------------------------------------------------------- #
# Layout

input_question = st.text_area(
    "Insights question",
    value="",
    placeholder="Example: What is the highest number of points scored in a single game by LeBron James ?",
)

input_trigger = st.button("Get an answer")
tab_result, tab_inspection = st.tabs(["Result", "Inspection"])

if input_trigger:
    clean_question = replace_names_in_text(input_question)
    tab_inspection.write(clean_question)

    sql_query = generate_sql_query(clean_question)
    tab_inspection.code(sql_query, language="sql")

    sql_query_result = sql_to_df(sql_query)
    tab_inspection.dataframe(sql_query_result)

    if len(sql_query_result) < 15:
        response_md = generate_question_response_md(question=clean_question, result=sql_query_result)
        tab_result.markdown(response_md)
    else:
        tab_result.dataframe(sql_query_result)
