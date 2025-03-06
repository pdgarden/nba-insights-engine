# -------------------------------------------------------------------------------------------------------------------- #
# Imports
from typing import Any, Literal, Optional

from loguru import logger
from openai import OpenAI

from app.configuration import config
from app.constants import DEFAULT_LLM_MAX_RETRIES, DEFAULT_LLM_TEMPERATURE


# -------------------------------------------------------------------------------------------------------------------- #
# Custom Exceptions
class LLMQueryError(Exception):
    """Exception raised for errors during LLM queries."""

    pass


# -------------------------------------------------------------------------------------------------------------------- #
# Models
def query_llm(
    prompt: str,
    model_kind: Literal["heavy", "light"],
    structured_output: Optional[Any] = None,
    temperature: float = DEFAULT_LLM_TEMPERATURE,
    max_retries: int = DEFAULT_LLM_MAX_RETRIES,
) -> Any:
    """
    Query the LLM with a prompt, using either the light or heavy model.
    """
    # Get configuration based on model kind
    try:
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
            raise ValueError(error_msg)  # noqa: TRY301

    except Exception as e:
        logger.error(f"Configuration error for {model_kind} model: {str(e)}")
        error_msg = f"Failed to get configuration for {model_kind} model"
        raise LLMQueryError(error_msg) from e

    # Initialize client
    client = OpenAI(base_url=url, api_key=api_key)

    # Retry logic for transient errors
    for attempt in range(max_retries):
        try:
            if structured_output is not None:
                # Structured output request
                response = client.beta.chat.completions.parse(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    response_format=structured_output,
                )
                return response.choices[0].message.parsed
            else:
                # Regular text request
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.warning(f"LLM query attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} LLM query attempts failed for {model_kind} model")
                error_msg = f"Failed to query {model_kind} LLM after {max_retries} attempts"
                raise LLMQueryError(error_msg) from e

    # This should never be reached due to the exception in the last retry attempt
    return None
