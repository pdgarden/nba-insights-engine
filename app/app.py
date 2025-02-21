"""Streamlit app to take a user question and return an answer by generating a SQL query executed on the database."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports

import streamlit as st

input_question = st.text_area(
    "Insights question",
    value="",
    placeholder="Example: What is the highest number of points scored in a single game by LeBron James ?",
)

input_trigger = st.button("Get an answer")

if input_trigger:
    st.write("TODO")
