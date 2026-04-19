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
- `done` `test/build/lint/type failure`: harden the mock HTTP test server shutdown path and socket reuse so address-provider tests stop flaking under CI timing and port reuse.
- `done` `test/build/lint/type failure`: make GitHub Actions coverage upload conditional so missing `CODECOV_TOKEN` no longer fails the entire matrix after successful tox runs.
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
- `gh auth status` -> blocked (`gh: command not found`)
- `gh run list --limit 5` -> blocked (`gh: command not found`)
- `.venv/bin/python -m tox -vv` -> success locally outside GitHub Actions; `tox-gh-actions` correctly reports it only overrides env selection when `GITHUB_ACTIONS=true`
- `.venv/bin/python - <<'PY' ... import yaml ... PY` -> blocked (`ModuleNotFoundError: No module named 'yaml'`)
- `.venv/bin/python -m pytest tests -q` -> success after workflow edit (`105 passed, 1 warning in 236.71s`)
- `rg -n "TODO|FIXME|XXX|HACK|not implemented|NotImplemented|stub|placeholder" zpywallet tests docs README.rst` -> reviewed; hits are existing internal notes, abstract-base guards, or generated docs, not a newly justified production blocker
- `.venv/bin/python -m tox -e flake8` -> success after workflow edit
- `.venv/bin/python -m tox -e docs` -> success after workflow edit
- `.venv/bin/python -m pytest tests -q` -> success on current tree (`105 passed, 1 warning in 211.38s`)
- `.venv/bin/python -m tox -e flake8` -> success on current tree
- `.venv/bin/python -m tox -e docs` -> success on current tree
- `env GITHUB_ACTIONS=true .venv/bin/python -m tox -vv` -> failed before fix; surfaced a flaky mock-server failure in `tests/test_09_address.py::TestAddress::test_000_btc_blockcypher_address` caused by port reuse and an ineffective shutdown request
- `.venv/bin/python -m pytest tests/test_09_address.py::TestAddress::test_000_btc_blockcypher_address -q` -> success after mock-server fix (`1 passed, 1 warning in 15.30s`)
- `.venv/bin/python -m pytest tests/test_09_address.py -q` -> success after mock-server fix (`7 passed, 1 warning in 24.70s`)
- `env GITHUB_ACTIONS=true .venv/bin/python -m tox -e py311,flake8,docs` -> success after mock-server fix (`py311`, `flake8`, and `docs` all passed)
- `.venv/bin/python -m pytest tests/test_09_address.py -q` -> success on current tree (`7 passed, 1 warning in 15.46s`)
- `env GITHUB_ACTIONS=true .venv/bin/python -m tox -e py311,flake8,docs` -> success on current tree (`py311`, `flake8`, and `docs` all passed in 240.83s`)
- `.venv/bin/python -m pytest tests -q` -> success on current tree (`105 passed, 1 warning in 226.81s`)
- `env GITHUB_ACTIONS=true .venv/bin/python -m tox -e py311,flake8,docs` -> success on current tree (`py311`, `flake8`, and `docs` all passed in 311.79s`)

## Current Iteration Summary
- Chosen task: verify the current tree against the repo-native completion bar after the CI flake fix, and confirm whether any justified in-scope work remains.
- In-scope evidence: `README.rst`, `tox.ini`, `.github/workflows/commit.yml`, and the existing tests define this library's completion bar as passing test, lint, and docs flows for the documented wallet, transaction, provider, and packaging paths.
- Changes made:
  - rechecked the current diffs and unfinished-work markers against the documented project scope
  - reran the full local test suite on the current tree
  - reran the CI-shaped `py311`, `flake8`, and `docs` tox environments with `GITHUB_ACTIONS=true` on the current tree
- Remaining work: no additional high-value, in-scope work is justified by the repository evidence in the available environment.

## Unresolved Blockers
- The repo still documents `python`-style commands, while this host only exposes `python3`; local validation therefore uses `.venv/bin/python`.
- GitHub CLI is unavailable in this workspace, so live Actions run inspection and log retrieval could not be performed from the runner side.

## Out Of Scope / Conservative Boundaries
- No new product features should be added beyond the existing wallet/transaction/network scope documented in README, tests, and current modules.
- Support for new coins/chains remains out of scope without direct repository evidence requiring it.
