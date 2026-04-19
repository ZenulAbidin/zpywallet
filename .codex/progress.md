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
- CI evidence: `.github/workflows/commit.yml` runs `python -m pip install -r requirements-dev.txt` then `tox` on Python 3.10-3.14.
- Local workspace constraints:
  - `python3` is available and works with `venv`.
  - The host Python is externally managed under PEP 668, so direct global `pip install` is blocked.
  - Local validation now runs in `.venv/` with repo-declared dev and runtime dependencies installed.
  - This branch currently tracks `.venv/` from an earlier baseline commit, so local tool installs dirty many environment files that are not part of the intended source changes.

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
- `done` `developer experience issue affecting completion`: repair the package/release path so `requirements-dev.txt` installs `build`, modern `twine`, correct package homepage metadata, and clean mnemonic package data without leaking cache artifacts into release archives.
- `done` `broken flow`: repair the documented BTC wallet send path so decrypted WIFs, fee policies, address-hash lookup, and segwit `nsequence` handling all work under the real `Wallet.create_transaction()` flow.
- `done` `security/validation/data integrity issue`: fix wallet-core helpers so `get_balance()` only counts confirmed UTXOs as confirmed and `random_address()` draws from the full configured receive gap instead of collapsing to a low-byte subset.
- `done` `security/validation/data integrity issue`: make `Transaction.sat_inputs()` and `sat_outputs()` return copies so witness data and output metadata stay stable across repeated public API calls.
- `todo` `security/validation/data integrity issue`: the EVM transaction wrapper still exposes stored `gas` as `gasUsed`, which looks semantically wrong for history/reporting.
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
- `.venv/bin/python -m build` -> failed before packaging fix (`No module named build`)
- `.venv/bin/python -m twine check dist/*` -> failed before packaging fix under `twine==4.0.2` (`KeyError: 'license'`)
- `.venv/bin/python -m pip install build 'twine>=5'` -> success; used to identify a working local release-tool version
- `.venv/bin/python -m pip install -r requirements-dev.txt` -> success after updating the dev-tool pins
- `.venv/bin/python -m pytest tests/test_04_mnemonic.py -q` -> success after packaging-data changes (`7 passed, 1 warning in 11.83s`)
- `.venv/bin/python -m build` -> success after packaging fixes; rebuilt clean `sdist` and wheel with the intended mnemonic assets
- `.venv/bin/python -m twine check dist/*` -> success after packaging fixes
- `python3 - <<'PY' ... inspect dist metadata and archive contents ... PY` -> success; both archives now advertise `https://github.com/ZenulAbidin/zpywallet` and contain zero cache artifacts
- `.venv/bin/python - <<'PY' ... wallet.create_transaction(...) with a mocked BTC UTXO ... PY` -> failed before fix (`AttributeError: 'str' object has no attribute 'decode'`), confirming the wallet-level BTC send path was still broken
- `.venv/bin/python -m pytest tests/test_06_wallet.py -q` -> failed before the segwit follow-up fix on the new wallet regression (`TypeError: fromhex() argument must be str, not bytes`), exposing a second send-path mismatch in `assemble_segwit_payload()`
- `.venv/bin/python -m pytest tests/test_06_wallet.py -q` -> success after the wallet-core fixes (`10 passed, 1 warning in 100.31s`)
- `.venv/bin/python -m flake8 --select=C,E,F,W,B,B950 --extend-ignore=W503,E203,E741,F401,E201 --exclude=zpywallet/generated --max-line-length=120 zpywallet/wallet.py zpywallet/destination.py zpywallet/transactions/encode.py tests/test_06_wallet.py` -> success
- `.venv/bin/python -m pytest tests/test_08_transaction.py -q` -> success after the segwit payload fix (`8 passed, 1 warning in 2.19s`)
- `.venv/bin/python -m pytest tests -q` -> success on the current wallet-core tree (`110 passed, 1 warning in 207.90s`)
- `.venv/bin/python -m tox -e flake8` -> success on the current wallet-core tree
- `.venv/bin/python - <<'PY' ... Transaction(...).sat_inputs(); Transaction(...).sat_inputs(include_witness=True) ... PY` -> failed before fix; the first call deleted witness data from the wrapper's cached input metadata
- `.venv/bin/python -m pytest tests/test_08_transaction.py -q` -> success after the transaction-wrapper copy fix (`10 passed, 1 warning in 2.40s`)
- `.venv/bin/python -m flake8 --select=C,E,F,W,B,B950 --extend-ignore=W503,E203,E741,F401,E201 --exclude=zpywallet/generated --max-line-length=120 zpywallet/transaction.py tests/test_08_transaction.py` -> success

## Current Iteration Summary
- Chosen task: harden the public `Transaction` wrapper after reproducing source-level data mutation in repeated `sat_inputs()` calls.
- In-scope evidence: `Transaction` objects are part of the documented wallet history API in `docs/source/usage.rst`, and callers are expected to be able to inspect inputs/outputs multiple times without altering cached metadata.
- Changes made:
  - changed `Transaction.sat_inputs()` to build copies of the cached input dicts and copy witness lists before optionally omitting them from the returned value
  - changed `Transaction.sat_outputs()` to return copies instead of exposing the wrapper's internal output dicts directly
  - added regression coverage proving witness data remains available after a prior `sat_inputs(include_witness=False)` call and that mutating returned outputs does not leak back into cached state
- Remaining work: the EVM history wrapper still appears to conflate stored `gas` with `gasUsed`, and that is the next justified data-integrity item.

## Unresolved Blockers
- The repo still documents `python`-style commands, while this host only exposes `python3`; local validation therefore uses `.venv/bin/python`.
- GitHub CLI is unavailable in this workspace, so live Actions run inspection and log retrieval could not be performed from the runner side.
- This branch tracks `.venv/` from earlier baseline work, so recreating tox envs or local installs may dirty environment files unrelated to the repository source. The current source edits across the active iterations are limited to `tests/test_06_wallet.py`, `tests/test_08_transaction.py`, `zpywallet/destination.py`, `zpywallet/transaction.py`, `zpywallet/transactions/encode.py`, and `zpywallet/wallet.py`.

## Out Of Scope / Conservative Boundaries
- No new product features should be added beyond the existing wallet/transaction/network scope documented in README, tests, and current modules.
- Support for new coins/chains remains out of scope without direct repository evidence requiring it.
- Local `.venv/` churn from validation is treated as workspace-only environment noise, not intended repository source work.
