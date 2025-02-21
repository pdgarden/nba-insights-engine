# NBA insights engine

- [NBA insights engine](#nba-insights-engine)
- [1. Project description](#1-project-description)
- [2. Prerequisites](#2-prerequisites)
- [3. Quickstart](#3-quickstart)
  - [3.1 Set up](#31-set-up)
  - [3.2 Run](#32-run)
  - [3.3. Environment variables](#33-environment-variables)
- [5. Dataset](#5-dataset)
- [6. Benchmarks](#6-benchmarks)
- [7 Code Quality and Formatting](#7-code-quality-and-formatting)
- [8. Improvements](#8-improvements)
- [9. Complementary documentation](#9-complementary-documentation)


# 1. Project description

The following repo implements an insights engine for NBA related data. A user asks a question through a web app, this 
generates a SQL query executed in backend. The query result is then used to answer to the user.

Example of questions:
- What is the highest number of points scored by lebron james in a single game?
- What are the top 5 players with the most points per games in the 2022-2023 season?



# 2. Prerequisites

The project uses:
- uv (`v0.5.10`) to handle python version and dependencies.
- ollama (`v0.5.5`) by default, but this can be replaced by any other LLM through env var settings.


# 3. Quickstart


## 3.1 Set up

1. Install uv (v0.5.10):
   1. For macOS / Linux `curl -LsSf https://astral.sh/uv/0.5.10/install.sh | sh`
   2. For windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.5.10/install.ps1 | iex"`
2. Create virtual environment: `uv sync --all-groups`
3. Make sure your environment variables are correctly set up to use your desired inference provider
4. To develop (Optional):
   1. Setup pre-commit: `uv run pre-commit install -t commit-msg -t pre-commit`


The lock file only contains dependencies necessary to run the Streamlit app.

## 3.2 Run

Once the set up is done, the app can be launched by executing the following command:

```sh
uv run python -m streamlit run app/insights_app.py
```

To run the benchmarks:
```sh
uv run python benchmark/benchmark_ner_retrieval_pipeline.py
```

```sh
uv run python benchmark/benchmark_request_to_sql.py
```


## 3.3. Environment variables


The app works with two LLMs: one _heavy llm_ for the SQL generation and one _light llm_ for easy tasks like NER and retrieval.

The interaction with the LLM (model and API provider) is configured using environment variables. By default the light LLM is set to use `qwen2.5:7b` with `ollama` and the heavy LLM is set to use `llama-3.3-70b-instruct` with `OpenRouter`. You can leave as is and just need to provide your `OpenRouter` API key in environment variable (see below). But you can also use any other model and API provider compliant with OpenAI SDK. Here is the list of environment variables you can set:

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| `LIGHT_LLM_BASE_URL` | Base URL of the light LLM API.\* | `http://localhost:11434/v1` |
| `LIGHT_LLM_API_KEY` | API key to connect to the light LLM API.\* | `ollama` |
| `LIGHT_LLM_MODEL` | Name of light LLM model used. Must be compatible with _structured_output_.\* | `qwen2.5:7b` |
| `HEAVY_LLM_BASE_URL` | Base URL of the heavy LLM API.\* | `https://openrouter.ai/api/v1` |
| `HEAVY_LLM_API_KEY` | API key to connect to the heavy LLM API.\* | *(Required)* |
| `HEAVY_LLM_MODEL` | Name of heavy LLM model used.\* | `meta-llama/llama-3.3-70b-instruct:free` |

_\* Used through OpenAI SDK._


To override the default values, you can set these environment variables directly in your environment, or in a `.env` file or at the repo's root. See .example in `env.example`


# 5. Dataset

The NBA database used is a duckdb database, generated using duckdb and dbt with this [repo](https://github.com/pdgarden/nba-stats).


# 6. Benchmarks

Some benchmark are available in the `benchmarks` folder for :
- The question cleaning (Players and teams Named Entity Recognition): `benchmark_ner_retrieval_pipeline.py`
- The SQL query generation based on the user question: `benchmark_request_to_sql.py`

For each benchmark, a small test set was created and a bunch of models were tested.


**Name entity recognition and retrieval pipeline results:**

| Model | Accuracy  |
|-------|---------- |
| smollm2:360m | 0% |
| llama3.2:3b | 90% |
| mistral:7b | 60%  |
| qwen2.5:7b | 100% |


**SQL generation pipeline results:**

| Model                                          | Accuracy  |
|----------------------------------------------- |---------- |
| meta-llama/llama-3.3-70b-instruct:free         | 81.25%    |
| mistralai/mistral-small-24b-instruct-2501:free | 56.25%    |

_TODO: Add results with deepseek V3 and reasoning models._

# 7 Code Quality and Formatting

- The python files are linted and formatted using ruff, see configuration in `pyproject.toml`
- Pre-commit configuration is available to ensure trigger quality checks (e.g. linter)
- Commit messages follow the conventional commit convention
- A CI/CD pipeline is implemented with github actions to lint the code


# 8. Improvements

- Handle `OPENROUTER_API_KEY` through .env file in the benchmark scripts
- Handle TODO tags
- Add retry mechanism on llm calls (when retrieve null value or incorrect SQL query)
- Test other models for request_to_sql
- Try autoencoders like BERT for ner_retrieval_pipeline
- Display plot based on generated result


# 9. Complementary documentation

- [Ollama](https://ollama.com/): To interact with the LLMs
- [OpenRouter](https://openrouter.ai/): To interact with the LLMs
