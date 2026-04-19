# Repository Guidelines

## Project Structure & Module Organization
Core library code lives in `zpywallet/`. Key areas include `address/`, `broadcast/`, `fees/`, `nodes/`, `transactions/`, and `utils/`. Tests live in `tests/`, with mock servers in `tests/mock/` and fixture data in `tests/data/`. Documentation sources are under `docs/source/`. Packaging files are at the repo root: `setup.py`, `setup.cfg`, `requirements*.txt`, and `tox.ini`. Treat `zpywallet/generated/wallet_pb2.py` as generated output tied to `wallet.proto`.

## Build, Test, and Development Commands
Install the dev toolchain with `python -m pip install -r requirements-dev.txt`.

- `tox`: run the full lint, docs, and multi-Python test matrix.
- `tox -e py312`: run the test suite on one interpreter.
- `tox -e flake8`: enforce the repository lint rules.
- `tox -e docs`: rebuild API docs and fail on Sphinx or `rstcheck` warnings.
- `python -m pytest tests/test_06_wallet.py`: run a focused test file during development.
- `python -m build`: build release artifacts, matching the publish workflow.

## Coding Style & Naming Conventions
Use 4-space indentation and Pythonic `snake_case` for modules, functions, and test methods; use `CapWords` for classes. Keep lines within the `flake8` limit of 120 characters. Follow existing import grouping and docstring style rather than introducing a new formatter. Exclude generated code in `zpywallet/generated/` from manual cleanup unless you are intentionally regenerating it.

## Testing Guidelines
Tests use `pytest`, `coverage`, and `pytest-benchmark`, with many cases written as `unittest.TestCase` classes. Add or extend tests in `tests/` for every behavioral change. Match the existing naming pattern: files like `test_08_transaction.py` and methods like `test_003_wallet_broadcast`. Run `tox` before opening a PR; coverage XML is produced automatically through tox.

## Commit & Pull Request Guidelines
Recent history favors short, imperative commit subjects such as `Update README.rst` or `make port selection more robust`. Keep each commit scoped to one change and avoid trailing punctuation. PRs should explain the behavior change, list tests run, and link any related issue. For network, transaction, or wallet-format changes, call out compatibility and migration risk explicitly. Per the project README, proposals for new coins are usually limited to major established networks.

## Security & Data Handling
Never commit real seed phrases, private keys, API tokens, or wallet exports. Use the existing test vectors and mocks instead of live secrets or production endpoints.

----

Current issues (non exhaustive list)

- Github actions for this repository fails completely. Please investigate the cause by replicating the tests locally, then fix the code or update the tests accordingly.

