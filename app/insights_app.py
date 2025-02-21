"""Streamlit app to take a user question and return an answer by generating a SQL query executed on the database."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports

import streamlit as st

from app.db import dao

# -------------------------------------------------------------------------------------------------------------------- #
# Layout

input_question = st.text_area(
    "Insights question",
    value="",
    placeholder="Example: What is the highest number of points scored in a single game by LeBron James ?",
)

input_trigger = st.button("Get an answer")

st.write(dao.get_player_names()[:5])
st.write(dao.get_team_names()[:5])


if input_trigger:
    st.write("TODO")
