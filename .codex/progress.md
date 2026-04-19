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
  - `python3` is available and works with `venv`.
  - The host Python is externally managed under PEP 668, so direct global `pip install` is blocked.
  - Local validation now runs in `.venv/` with repo-declared dev and runtime dependencies installed.
  - A local `.venv/` exists for validation but is an untracked environment artifact, not repository source.

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
- `done` `developer experience issue affecting completion`: create a local `.venv` and install repo-declared tooling so runtime validation works under PEP 668.
- `done` `broken flow`: remove wasted PBKDF2 work in `zpywallet/utils/aes.py` that made wallet create/deserialize paths unreasonably slow.
- `done` `test/build/lint/type failure`: add regression coverage proving the optimized PBKDF2 output matches the legacy-derived prefix used by wallet encryption.
- `done` `broken flow`: make broadcast fan-out actually concurrent so public-node propagation no longer serializes blocking network calls across every provider.
- `out_of_scope` `polish`: existing TODO/XXX comments in provider internals are not tied to a current failing core flow and were left unchanged.

## Validations Attempted
- `python3 --version` -> success (`3.11.2`)
- `python3 -m pip --version` -> success
- `python3 -m pytest --version` -> failed (`No module named pytest`)
- `python3 - <<'PY' ... import zpywallet ... PY` -> failed (`No module named 'Cryptodome'`)
- `python3 -m py_compile zpywallet/transactions/encode.py` -> success
- `python3 -m venv .venv && .venv/bin/python -m pip install -r requirements-dev.txt -r requirements.txt` -> success
- `timeout 30s .venv/bin/python -u - <<'PY' ... Wallet(...) / serialize() / deserialize() ... PY` -> success after PBKDF2 optimization; wallet create in about 8s and deserialize in about 6s
- `.venv/bin/python -m pytest tests/test_08_transaction.py -q` -> success (`8 passed`)
- `.venv/bin/python -m pytest tests/test_06_wallet.py -k 'not test_003_wallet_broadcast' -q` -> success (`5 passed, 1 deselected`)
- `.venv/bin/python -m pytest tests/test_05_zpywallet.py -k 'test_009_pbkdf2_default_length_matches_legacy_prefix or test_000_create_wallet' -q` -> success (`2 passed`)
- `.venv/bin/python -m pytest tests/test_05_zpywallet.py tests/test_06_wallet.py tests/test_08_transaction.py -k 'not test_003_wallet_broadcast' -q` -> success (`23 passed, 1 deselected`)
- `.venv/bin/python -m flake8 --select=C,E,F,W,B,B950 --extend-ignore=W503,E203,E741,F401,E201 --exclude=zpywallet/generated --max-line-length=120 zpywallet/utils/aes.py tests/test_05_zpywallet.py` -> success
- `.venv/bin/python -m pytest tests/test_06_wallet.py -k 'test_000_create_wallet or test_005_eth_wallet_create_transaction or test_006_wallet_broadcast_runs_providers_concurrently' -q` -> success (`3 passed, 4 deselected`)
- `.venv/bin/python -m pytest tests/test_08_transaction.py -q` -> success (`8 passed`)
- `.venv/bin/python -m flake8 --select=C,E,F,W,B,B950 --extend-ignore=W503,E203,E741,F401,E201 --exclude=zpywallet/generated --max-line-length=120 zpywallet/broadcast zpywallet/utils/aes.py` -> success
- `.venv/bin/python -m pytest tests/test_05_zpywallet.py tests/test_06_wallet.py tests/test_08_transaction.py -k 'not test_003_wallet_broadcast' -q` -> success (`24 passed, 1 deselected`)
- `.venv/bin/python -m pytest tests -q` -> success (`105 passed, 1 warning`)
- `.venv/bin/python -m tox -e flake8` -> success
- `.venv/bin/python -m tox -e docs` -> success

## Current Iteration Summary
- Chosen task: confirm whether any justified in-scope work remained after the wallet encryption and broadcast fixes by running the repo-native validation stack end to end.
- In-scope evidence: `README.rst`, `tox.ini`, and `.github/workflows/commit.yml` define this project as a Python library whose expected completion bar is passing tests, lint, and docs for the documented wallet/transaction flows.
- Changes made:
  - created the required session baseline commit `ddf9e04` (`chore: baseline before autonomous work`) for the existing source changes before further edits
  - revalidated the entire local test suite with `.venv/bin/python -m pytest tests -q`
  - revalidated the repo-native lint and docs flows with `.venv/bin/python -m tox -e flake8` and `.venv/bin/python -m tox -e docs`
- Remaining work: none justified by current repository evidence; the documented library scope now validates locally.

## Unresolved Blockers
- The repo still documents `python`-style commands, while this host only exposes `python3`; local validation therefore uses `.venv/bin/python`.

## Out Of Scope / Conservative Boundaries
- No new product features should be added beyond the existing wallet/transaction/network scope documented in README, tests, and current modules.
- Support for new coins/chains remains out of scope without direct repository evidence requiring it.
