from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    light_llm_base_url: str = Field(
        description="Base URL of the light LLM API. Used through OpenAI SDK.",
        default="http://localhost:11434/v1",
    )
    light_llm_api_key: SecretStr = Field(
        description="API key to connect to the light LLM API. Used through OpenAI SDK.",
        default="ollama",
    )
    light_llm_model: str = Field(
        description="Name of light LLM model used. Used through OpenAI SDK.",
        default="qwen2.5:7b",
    )

    heavy_llm_base_url: str = Field(
        description="Base URL of the heavy LLM API. Used through OpenAI SDK.",
        default="https://openrouter.ai/api/v1",
    )
    heavy_llm_api_key: SecretStr = Field(
        description="API key to connect to the heavy LLM API. Used through OpenAI SDK.",
    )

    heavy_llm_model: str = Field(
        description="Name of heavy LLM model used. Used through OpenAI SDK.",
        default="meta-llama/llama-3.3-70b-instruct:free",
    )


config = Config(_env_file=".env")
