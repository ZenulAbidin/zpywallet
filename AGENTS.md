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

give me an honest opinion about github.com/zenulabidin/zpywallet in order to determine whether it is readyfor production grade Bitcoin-like and Ethereum EVM chainusage inwallets (i.e. can thispower a wallet)?

My honest opinion: **no, not as-is**. I would not call `zpywallet` production-grade wallet infrastructure today. It looks like a serious **beta/prototype** library rather than a battle-hardened wallet core: the README says “This is beta software,” PyPI classifies it as **Beta**, the latest PyPI release I found is **0.6.2 from January 30, 2024**, and the project’s own security docs say it **has not been audited**. The maintainer also opened an issue saying the wallet should not be “officially endorsed for production use” until a security or cryptography expert reviews the sensitive parts of the design. citeturn866146view3turn281164view4turn866146view4turn866146view1turn866146view5

That does not mean it is junk. It has real documentation, a tests directory, CI via GitHub Actions with a tox matrix across Python 3.8–3.12, and it uses standard primitives like `libsecp256k1` and `os.urandom`. Those are good signs. But for wallet software, “good signs” are not the same as “safe to put user funds behind.” citeturn657046view0turn383213view0turn866146view1

For **Bitcoin-like chains**, the supported scope is much narrower than I would want in a production wallet. The README says Taproot, P2WSH, and P2WPKH-P2SH can be **decoded but not created**; multisig is unsupported; timelocks are unsupported. The limitations docs also say it **cannot send from script hashes** such as P2SH and P2WSH. That leaves you with a relatively restricted single-sig wallet feature set, which may be fine for a demo app but not for a broadly capable wallet product. citeturn281164view1turn281164view2turn866146view0

For **EVM**, my answer is a clearer **no**. The usage docs list `EthereumMainNet` and explicitly say it **does not support smart contracts**. The limitations page says **contract addresses are not officially supported**. The maintainer’s own issue tracker says only Ethereum mainnet, and only **limited Sepolia**, are supported, while support for chains like **BSC, Polygon, and Base** still needs to be added. In the code path I inspected, EVM signing goes through a `create_web3_transaction()` function that builds a basic native transfer dict with fields like `nonce`, `to`, `value`, `chain_id`, and `gas`, which matches a simple ETH transfer much more than a general-purpose EVM wallet engine. citeturn866146view2turn281164view8turn866146view6turn152946view0

A bigger red flag for money-handling code: the docs explicitly say `Destination` takes **floating-point amounts**, not integer sats or wei, and warn that amounts can be slightly wrong—especially for Ethereum, which uses 18 decimals. For production wallet code, integer-denominated accounting is the baseline, not an optional refinement. citeturn866146view0

The test story is also not convincing enough for me. There is a test suite and CI, which is positive, but the EVM tests I checked are shallow: one wallet test literally patches `create_transaction` to return `b"signed"`, and another uses a fake Web3 object and only checks that `raw_transaction` equals `b"signed"`. That is useful as wiring verification, but it is not the kind of end-to-end transaction assurance I would want before trusting real funds. citeturn657046view0turn383213view0turn383213view4turn192998view4

I also saw signs of **docs/code drift**. The usage docs say the wallet “does not currently make use of change addresses,” but later on the same page say “Change output is automatically calculated by the wallet.” Separately, the codebase defines an `EthereumSepoliaTestNet` class, but `wallet.py`’s network map only includes `ETHEREUM_MAINNET`, while the public usage docs still only list `EthereumMainNet`. That kind of mismatch is survivable in a hobby or beta project; in production wallet software it is a trust problem. citeturn281164view10turn281164view11turn192998view3turn383904view1turn866146view2

One concrete code-level concern from my own read: `random_address()` computes the RNG byte length as `ceil(log2(len(addresses))) // 8`. With the default `receive_gap_limit=1000`, that means it reads **one byte**, so only indices **0–255** can ever be selected; the rest of the generated addresses are unreachable through that method. That is my inference from the code, not a maintainer-stated bug, but it is exactly the kind of thing I would want fixed before using the library in production. citeturn192998view0turn192998view1turn383904view3

So: **can it power a wallet?** In a narrow sense, yes. I could imagine using it for a prototype, an internal tool, or a tightly scoped single-sig BTC-like / native-ETH wallet after a fork and heavy review. But in the sense most teams mean by **production-grade wallet backend**, especially across both **Bitcoin-like chains and EVM chains**, my answer is **no**. I would not ship it unmodified as the core of a wallet holding real user funds. citeturn866146view3turn281164view1turn866146view2turn866146view0turn866146view5

What would change my answer: an external security audit, integer-only amount handling, deeper Bitcoin feature coverage or a much narrower explicitly-supported scope, much stronger EVM support, real integration tests against live/regtest/testnet environments, and cleanup of the docs/code inconsistencies. If you’re making a go/no-go decision today, I’d treat `zpywallet` as **interesting beta software**, not wallet-grade infrastructure.

Isthatthe only issue you found? you should definitely read thesource code and not rely solely on readme and documentation metadata alone.

No. After reading the source, I think my first answer was too generous.

The biggest source-level problems I found are these:

* The ordinary **Bitcoin-like wallet send path looks internally broken in multiple places**. `Wallet.private_keys()` returns JSON-decoded private keys, but `_to_human_friendly_utxo()` calls `private_key.decode()`. Later, the signer calls `i.key_hash()`, while the `UTXO` class in the repo exposes `_addresshash()` and not `key_hash()`. And `_calculate_change()` calls `o.fee_policy()`, but the `Destination` class stores `_fee_policy` and only defines `address()`, `amount()`, and `script_pubkey()`. In normal Python execution, those mismatches point to runtime failures in the core transaction path. ([GitHub][1])

* The **amount/fee accounting is unsafe**. In `Destination.amount(False)`, raw units are produced by multiplying `_amount` by `1e8` or `1e18`, which means `_amount` is effectively being treated as BTC/ETH-style standard units. But `_calculate_change()` subtracts a raw `proportional_fee` directly from `o._amount`, mixing raw units with standard units. The same code path also accepts `fee_rate=None` from `Wallet.create_transaction()` and then immediately uses `size * fee_rate`, so there is no safe default fee-estimation path there. ([GitHub][2])

* **Address and change handling are not wallet-grade**. The wallet stores `change_gap_limit`, but the derivation loop shown in `wallet.py` only generates `.../0/i` addresses, and change is later sent to `Destination(self.random_address(), ...)` instead of a dedicated change branch. On top of that, `random_address()` computes the RNG byte count as `ceil(log2(n)) // 8`; by inspection, that means small wallets can collapse to zero bytes of randomness and larger wallets are still heavily biased, so address selection is not uniform. ([GitHub][1])

* The **UTXO/balance path is inconsistent enough to be fragile**. `Wallet.get_utxos()` iterates indices over `t.sat_outputs(only_unspent=only_unspent)`, but `UTXO.__init__()` always reindexes into `transaction.sat_outputs(only_unspent=True)` and can raise `IndexError`; `get_utxos()` only catches `ValueError`, not `IndexError`. Because `get_balance()` depends on `get_utxos()`, I would not trust balance handling around transactions that mix spent and unspent outputs. Also, `confirmed_balance` is summed from `get_utxos(only_unspent=True)` without a confirmation check, so the confirmed/total split itself looks wrong to me. That last point is my inference from the code flow. ([GitHub][1])

* I would **not trust script-hash handling**. `PublicKey.address_script()` returns the same P2PKH-style script for both `PUBKEY_ADDRESS` and `SCRIPT_ADDRESS`, and `script_is_p2sh()` checks `script[24]` on a 23-byte script. Even before getting to broader feature gaps, those helpers are not what I would want under real funds. ([GitHub][3])

* On the **EVM side**, the implementation is narrower and less correct than a production wallet core should be. The encoder uses only `outputs[0]` for EVM transactions, so extra destinations are silently ignored. In the indexer, `element["gas"]` is stored into `ethlike_transaction.gas`, total fees are computed from that same value, and `Transaction` later exposes it as `gasUsed`; that looks like gas-limit metadata being presented as gas-used metadata. There is also an `EthereumSepoliaTestNet` class in `network.py`, but `wallet.py` only maps `EthereumMainNet`, which suggests support is not wired cleanly end to end. ([GitHub][4])

* The **tests do not offset these concerns**. The wallet-level EVM transaction test patches `zpywallet.wallet.create_transaction` to return `b"signed"`, and the lower-level EVM signing test only checks a fake `{"raw_transaction": b"signed"}` object. Several BTC transaction tests only execute the core signing call when `len(utxos) > 0`, which weakens coverage of the real happy path. ([GitHub][5])

So no, those were definitely **not** the only issues. After actually reading the code, my view is stronger: **I would not use this as the transaction/balance core of a production wallet**, especially not for Bitcoin-like chains. For EVM, I would also not use it as a general wallet engine beyond very narrow native-transfer experiments. The safest description is: **interesting beta code, but not wallet-core infrastructure**.

[1]: https://github.com/ZenulAbidin/zpywallet/blob/master/zpywallet/wallet.py "zpywallet/zpywallet/wallet.py at master · ZenulAbidin/zpywallet · GitHub"
[2]: https://github.com/ZenulAbidin/zpywallet/blob/master/zpywallet/destination.py "zpywallet/zpywallet/destination.py at master · ZenulAbidin/zpywallet · GitHub"
[3]: https://github.com/ZenulAbidin/zpywallet/blob/master/zpywallet/utils/keys.py "zpywallet/zpywallet/utils/keys.py at master · ZenulAbidin/zpywallet · GitHub"
[4]: https://github.com/ZenulAbidin/zpywallet/blob/master/zpywallet/transactions/encode.py "zpywallet/zpywallet/transactions/encode.py at master · ZenulAbidin/zpywallet · GitHub"
[5]: https://raw.githubusercontent.com/ZenulAbidin/zpywallet/master/tests/test_06_wallet.py "raw.githubusercontent.com"


I'm the maintainer. Give me advice onwhat needsto be done urgently.

Yes — after reading the current source, I’d treat these as the **urgent release blockers**.

1. **Fix the Bitcoin send path before anything else.**
   Right now the ordinary BTC-like wallet flow appears broken by direct API mismatches: `private_keys()` returns JSON-decoded strings, but `_to_human_friendly_utxo()` calls `private_key.decode()`; `_calculate_change()` calls `o.fee_policy()`, but `Destination` does not define that method; the encoder calls `i.key_hash()`, while `UTXO` exposes `_addresshash()` instead; and `_calculate_change()` multiplies `size * fee_rate` even though `Wallet.create_transaction()` defaults `fee_rate=None`. I would treat that whole path as non-working until an end-to-end regtest signs and serializes a real transaction. ([GitHub][1])

2. **Remove floats from the core money model.**
   `Destination.amount(False)` converts by multiplying `_amount` by `1e8` or `1e18`, so the core model is using human units and float-style arithmetic at the transaction layer. Then `_calculate_change()` subtracts raw fees directly from `o._amount`, and later hardcodes `change / 1e8` when building the change output. I would switch the entire internal model to integer satoshis/wei immediately, and only convert at the UI/API boundary. ([GitHub][2])

3. **Fix script generation for script-hash outputs.**
   `PublicKey.address_script()` currently builds the same P2PKH-style script for both pubkey-hash and script-hash addresses, and `script_is_p2sh()` checks `script[24]` on a 23-byte script. That means I would not trust P2SH handling until it is corrected and covered by tests. ([GitHub][3])

4. **Implement real change handling, not “random wallet address” change.**
   The wallet derives only `.../0/i` addresses in the constructor and sends change to `random_address()` instead of a dedicated internal/change branch. On top of that, `random_address()` computes the RNG byte length as `ceil(log2(n)) // 8`; by my reading, that makes the selection deterministic or badly biased for many wallet sizes. I would derive external and internal chains separately and make change deterministic on the internal branch. ([GitHub][1])

5. **Repair UTXO and balance accounting.**
   `get_balance()` adds every unspent output into `confirmed_balance` without checking confirmation status. Separately, `get_utxos()` iterates indexes over `sat_outputs(only_unspent=...)`, but `UTXO.__init__()` reindexes into `transaction.sat_outputs(only_unspent=True)`, which can misalign indexes or raise when spent and unspent outputs are mixed. That is the kind of bug that creates false balances, which is wallet-fatal. ([GitHub][1])

6. **Make the EVM send/broadcast contract internally consistent.**
   The EVM encoder only uses `outputs[0]`, so extra destinations are silently ignored. It returns the direct result of `w3.eth.account.sign_transaction(...)`, while the current web3.py docs show the broadcast flow as sending `signed.raw_transaction`; your ETH broadcaster normalizes bytes/hex strings, not SignedTransaction objects. I would either return raw tx bytes/hex from `Wallet.create_transaction()` or make `Wallet.broadcast_transaction()` extract `.raw_transaction` explicitly. ([GitHub][4])

7. **Either wire EVM history/indexing all the way through, or stop advertising it for now.**
   The wallet turns on `use_database=True` for EVM and `Web3Client.get_transaction_history()` reads from `SQLTransactionStorage`, but the public `Wallet` constructor/setup only threads through node/token kwargs and does not pass `db_connection_parameters`. In the client stack, the DB config is expected when database mode is used. So from the public wallet API, that path is not actually wired end to end. ([GitHub][1])

8. **Upgrade the tests from smoke tests to regression tests around the real critical path.**
   The current wallet-level EVM test patches `zpywallet.wallet.create_transaction` to return `b"signed"`, so it does not exercise the real signer/broadcast contract at all. I would add one real Bitcoin regtest signing test, one native ETH devnet test, and regression tests for each bug above before touching new chains or new features. ([GitHub][5])

There are two more fixes I’d put right behind those: `Transaction.sat_inputs()` mutates internal state by deleting witness data from stored inputs, and the EVM transaction wrapper labels stored `gas` as `gasUsed`, while the indexer fills it from the transaction’s `gas` field rather than a receipt. Those are not my first blockers, but they are worth fixing before you ask anyone to trust balances, history, or signing outputs. ([GitHub][6])

If I were triaging the project, I would **not add more networks yet**. I would first make **one BTC-like send path** and **one native ETH send path** correct, deterministic, integer-only, and integration-tested.

[1]: https://raw.githubusercontent.com/ZenulAbidin/zpywallet/master/zpywallet/wallet.py "raw.githubusercontent.com"
[2]: https://raw.githubusercontent.com/ZenulAbidin/zpywallet/master/zpywallet/destination.py "raw.githubusercontent.com"
[3]: https://raw.githubusercontent.com/ZenulAbidin/zpywallet/master/zpywallet/utils/keys.py "raw.githubusercontent.com"
[4]: https://raw.githubusercontent.com/ZenulAbidin/zpywallet/master/zpywallet/transactions/encode.py "raw.githubusercontent.com"
[5]: https://raw.githubusercontent.com/ZenulAbidin/zpywallet/master/tests/test_06_wallet.py "raw.githubusercontent.com"
[6]: https://raw.githubusercontent.com/ZenulAbidin/zpywallet/master/zpywallet/transaction.py "raw.githubusercontent.com"


