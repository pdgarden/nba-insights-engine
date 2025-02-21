"""Interaction with the llm"""

# -------------------------------------------------------------------------------------------------------------------- #
# Imports
from typing import Any, Literal

from openai import OpenAI

from app.configuration import config

# -------------------------------------------------------------------------------------------------------------------- #
# Models


def query_llm(
    prompt: str,
    model_kind: Literal["heavy", "light"],
    structured_output: Any = None,
) -> Any:
    """Query the llm with a prompt, could be either the light or heavy model. Handle the structured output if needed.

    If using structured output, make sure that the inference engine supports it.
    """

    if model_kind == "heavy":
        url = config.heavy_llm_base_url
        model = config.heavy_llm_model
        api_key = config.heavy_llm_api_key.get_secret_value()

    elif model_kind == "light":
        url = config.light_llm_base_url
        model = config.light_llm_model
        api_key = config.light_llm_api_key.get_secret_value()

    else:
        error_msg = f"Unknown model kind: {model_kind}"
        raise ValueError(error_msg)

    client = OpenAI(base_url=url, api_key=api_key)

    if structured_output is not None:
        response = (
            client.beta.chat.completions.parse(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format=structured_output,
            )
            .choices[0]
            .message.parsed
        )
    # TODO: Add error handling

    else:
        response = (
            client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
            .choices[0]
            .message.content
        )

    return response
