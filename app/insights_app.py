"""Streamlit app to take a user question and return an answer by generating a SQL query executed on the database."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports

import streamlit as st

from app.db.connection import con

# -------------------------------------------------------------------------------------------------------------------- #
# Layout

input_question = st.text_area(
    "Insights question",
    value="",
    placeholder="Example: What is the highest number of points scored in a single game by LeBron James ?",
)

input_trigger = st.button("Get an answer")

st.write(con.sql("select 1+1;"))

if input_trigger:
    st.write("TODO")
