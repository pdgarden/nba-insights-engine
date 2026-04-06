"""Functions to choose how to display the result of a query."""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports

from enum import StrEnum
from typing import Literal

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from pydantic import BaseModel, Field

from app.constants import CHART_HEIGHT, CHART_TEMPLATE, CHART_WIDTH
from app.llm import query_llm
from app.prompts import CHART_CONFIG

# -------------------------------------------------------------------------------------------------------------------- #
# Models


class ChartType(StrEnum):
    LINE = "LINE"
    SCATTER = "SCATTER"
    BAR = "BAR"


class LineChartConfig(BaseModel):
    chart_type: Literal[ChartType.LINE] = Field(default=ChartType.LINE, description="Chart type identifier")
    x_col: str = Field(description="Column for x-axis (typically time/ordinal)")
    y_col: str = Field(description="Column for y-axis (numerical values)")
    color_col: str | None = Field(default=None, description="Column to group/color lines")


class ScatterChartConfig(BaseModel):
    chart_type: Literal[ChartType.SCATTER] = Field(default=ChartType.SCATTER, description="Chart type identifier")
    x_col: str = Field(description="Column for x-axis (numerical)")
    y_col: str = Field(description="Column for y-axis (numerical)")
    color_col: str | None = Field(default=None, description="Column for color encoding")
    size_col: str | None = Field(default=None, description="Column for size encoding")
    symbol_col: str | None = Field(default=None, description="Column for symbol encoding")


class BarChartConfig(BaseModel):
    chart_type: Literal[ChartType.BAR] = Field(default=ChartType.BAR, description="Chart type identifier")
    x_col: str = Field(description="Column for x-axis (typically categories)")
    y_col: str = Field(description="Column for y-axis (values)")
    color_col: str | None = Field(default=None, description="Column for color encoding")
    orientation: str | None = Field(default=None, description="Chart orientation: 'v' (vertical) or 'h' (horizontal)")


class CommonChartConfig(BaseModel):
    x_axis_label: str = Field(description="Label displayed for x-axis")
    y_axis_label: str = Field(description="Label displayed for y-axis")
    title: str = Field(description="Title of the chart")


class ChartConfig(BaseModel):
    chart_type_config: LineChartConfig | ScatterChartConfig | BarChartConfig = Field(discriminator="chart_type")
    chart_common_config: CommonChartConfig = Field(description="Common chart configuration")


class ChartDecision(BaseModel):
    """Either a chart configuration or False (meaning no chart should be displayed)"""

    chart: ChartConfig | Literal[False] = Field(
        description="Chart configuration if a chart should be displayed, or False if no visualization is appropriate"
    )


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


def generate_chart_decision(user_query: str, sql_query: str, df: pd.DataFrame) -> ChartDecision:
    """Use an LLM to decide if a chart should be displayed and which configuration to use."""
    # Format the DataFrame info for the prompt
    df_shape = f"({df.shape[0]} rows, {df.shape[1]} columns)"
    df_dtypes = "\n".join([f"- {col}: {dtype}" for col, dtype in df.dtypes.items()])

    # Format the prompt with all context
    prompt = CHART_CONFIG.format(
        user_query=user_query,
        sql_query=sql_query,
        df_shape=df_shape,
        df_dtypes=df_dtypes,
        output_json_schema=ChartDecision.model_json_schema(),
    )

    # Query the LLM with structured output
    return query_llm(prompt=prompt, model_kind="light", structured_output=ChartDecision)


def render_chart(df: pd.DataFrame, chart_config: ChartConfig) -> Figure:
    """Render a chart based on the ChartConfig using Plotly Express."""
    type_config = chart_config.chart_type_config
    common_config = chart_config.chart_common_config
    chart_type_to_function = {ChartType.LINE: px.line, ChartType.SCATTER: px.scatter, ChartType.BAR: px.bar}

    try:
        chart_function = chart_type_to_function[type_config.chart_type]
    except KeyError as exc:
        error_msg = f"Unknown chart type: {type_config.chart_type}"
        raise ValueError(error_msg) from exc

    # Build common chart arguments
    chart_kwargs = {
        "data_frame": df,
        "x": type_config.x_col,
        "y": type_config.y_col,
        "color": type_config.color_col,
        "hover_data": df.columns,
        "width": CHART_WIDTH,
        "height": CHART_HEIGHT,
        "template": CHART_TEMPLATE,
    }

    # Add chart-type specific arguments
    if isinstance(type_config, ScatterChartConfig):
        if type_config.size_col:
            chart_kwargs["size"] = type_config.size_col
        if type_config.symbol_col:
            chart_kwargs["symbol"] = type_config.symbol_col
    elif isinstance(type_config, BarChartConfig) and type_config.orientation:
        chart_kwargs["orientation"] = type_config.orientation

    # Create the chart
    chart = chart_function(**chart_kwargs).update_layout(
        title=common_config.title,
        xaxis_title=common_config.x_axis_label,
        yaxis_title=common_config.y_axis_label,
    )

    return chart
