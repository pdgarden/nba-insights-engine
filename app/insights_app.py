"""Streamlit app to take a user question and return an answer by generating a SQL query executed on the database."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports

import streamlit as st

from app.db.dao import sql_to_df
from app.logic.ner_retrieval import replace_names_in_text
from app.logic.question_to_sql import generate_sql_query

# -------------------------------------------------------------------------------------------------------------------- #
# Layout

input_question = st.text_area(
    "Insights question",
    value="",
    placeholder="Example: What is the highest number of points scored in a single game by LeBron James ?",
)

input_trigger = st.button("Get an answer")

if input_trigger:
    clean_question = replace_names_in_text(input_question)
    sql_query = generate_sql_query(clean_question)
    sql_query_result = sql_to_df(sql_query)

    st.write(clean_question)
    st.write(sql_query)
    st.dataframe(sql_query_result)
