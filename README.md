# README

TODO

# App

Run:
```sh
uv run python -m streamlit run app/app.py
```


# Benchmark

To run the benchmarks for ner_retrieval pipeline, make sure that ollama is available with the correct models installed (list of tested model available in the script's constants part).
```sh
uv run python benchmark/benchmark_ner_retrieval_pipeline.py
```

or

To run the benchmarks for ner_retrieval pipeline, make sure that the env variable `OPENROUTER_API_KEY` is in your environment

```sh
uv run python benchmark/benchmark_request_to_sql.py
```

Will benchmark a list of chosen models, and save the result in `data/benchmark/results/`


# Improvements

- Handle OPENROUTER_API_KEY through .env file in the benchmark scripts
