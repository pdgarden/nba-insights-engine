# README

TODO


# Benchmark

Run:
Make sure that ollama is available with the correct models installed (list of tested model available in the script's constants part).
```sh
uv run python benchmark/benchmark_ner_retrieval_pipeline.py
```

Will benchmark a list of chosen models, and save the result in `data/benchmark/results/`
