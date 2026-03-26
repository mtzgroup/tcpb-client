# Contributing

## Developing

If you already cloned the repository and you know that you need to deep dive in the code, here are some guidelines to set up your environment.

Note that lots of apparently unused code was removed from the repo to clean it up and make clear the actual code under development. To review all old code previously in the repo checkout the `r0.6.0` tag.

### Environment

`tcpb` uses `uv` for dependency management and development workflows.

Install project and development dependencies with:

```console
$ uv sync --group dev
```

This creates a local virtual environment in `.venv/` and installs the package in editable mode.

Use project commands through `uv run`:

```console
$ uv run pytest
$ uv run ruff check .
```

## Tests

Use `pytest` to test all the code.

```console
uv run pytest
```

This command requires a TeraChem server running on the host and server set in `tests/conftest.py`, `localhost` and port `11111` by default. Often running a TeraChem server on Fire and using port forwarding is the easiest way to accomplish this. Tests in the `tests/test_utils.py` file do not require a TeraChem server.
