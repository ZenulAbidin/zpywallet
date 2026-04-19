# Progress

## Inferred Project Identity
- Project type: Python library for hierarchical deterministic cryptocurrency wallets and transaction management.
- Intended users: developers integrating wallet generation, transaction signing/broadcasting, address monitoring, and fee lookup into their own software.
- Current scope: multi-network wallet/key generation, transaction creation and decoding, network broadcasting, address monitoring, and docs/tests for the supported networks already present in the repo.

## Environment And Tooling
- Languages: Python, Protocol Buffers generated Python, reStructuredText docs.
- Packaging/build: `setuptools` via `setup.py`, `setup.cfg`, `python -m build`.
- Dependency management: `pip` with `requirements.txt` and `requirements-dev.txt`.
- Validation: `tox`, `pytest`, `coverage`, `flake8`, `Sphinx`, `rstcheck`.
- CI evidence: `.github/workflows/commit.yml` runs `python -m pip install -r requirements-dev.txt` then `tox` on Python 3.8-3.12.
- Local workspace constraints:
  - `python3` is available.
  - `python` command is not available.
  - `pytest` and `tox` are not installed yet in the current environment.
  - Runtime dependencies such as `Cryptodome` are not installed, so importing the package currently fails locally.

## Likely Validation Commands
- Install/setup: `python3 -m pip install -r requirements-dev.txt`
- Tests: `python3 -m tox` or `python3 -m pytest tests`
- Focused tests: `python3 -m pytest tests/test_06_wallet.py`
- Lint: `python3 -m tox -e flake8`
- Docs: `python3 -m tox -e docs`
- Build: `python3 -m build`

## Core User Flows
- Generate mnemonic phrases and HD wallets.
- Serialize/deserialize wallets and restore addresses/keys.
- Create UTXO and EVM transactions.
- Broadcast signed transactions to supported providers/nodes.
- Query balances, UTXOs, fees, and address history through providers.

## Backlog
- `done` `broken flow`: fix transaction creation loop in `zpywallet/transactions/encode.py` so list inputs can be signed.
- `todo` `test/build/lint/type failure`: install repo-declared tooling and run targeted wallet/transaction tests.
- `todo` `broken flow`: continue searching for transaction and wallet regressions after local toolchain is available.
- `blocked` `developer experience issue affecting completion`: current workspace lacks package/test dependencies, so meaningful runtime validation is blocked until installed.

## Validations Attempted
- `python3 --version` -> success (`3.11.2`)
- `python3 -m pip --version` -> success
- `python3 -m pytest --version` -> failed (`No module named pytest`)
- `python3 - <<'PY' ... import zpywallet ... PY` -> failed (`No module named 'Cryptodome'`)
- `python3 -m py_compile zpywallet/transactions/encode.py` -> success

## Current Iteration Summary
- Chosen task: repair the central UTXO transaction construction loop.
- In-scope evidence: `README.rst` and `tests/test_08_transaction.py` both define signed transaction creation as a core library flow.
- Change made: replaced `range(inputs)` with `range(len(inputs))` in `zpywallet/transactions/encode.py` so list-based inputs are iterable in the signing loop.
- Remaining work: install repo-declared dependencies, run targeted wallet/transaction tests, then continue scanning for any further wallet/transaction regressions.

## Unresolved Blockers
- Missing local dependencies from `requirements.txt` / `requirements-dev.txt` prevent import-time and test-time validation.
- No `.codex/progress.md` existed before this iteration; it has now been created to preserve state for future iterations.

## Out Of Scope / Conservative Boundaries
- No new product features should be added beyond the existing wallet/transaction/network scope documented in README, tests, and current modules.
- Support for new coins/chains remains out of scope without direct repository evidence requiring it.
