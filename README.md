# RUAX- CAI Credit Audit State Machine

**Author:** Michael Aaron Russell ([ORCID 0009-0001-3360-6709](https://orcid.org/0009-0001-3360-6709))

A deterministic, integer-only (10^18 fixed-point) state machine for auditing credit-report data. The Python implementation is the canonical reference, and `src/CreditAuditSM.sol` mirrors it. Every run prints its full intermediate math (the Trace).

> **Not FICO or VantageScore.** Those algorithms are proprietary and unpublished. This capsule implements only the publicly documented factor weights (35/30/15/10/10) and the standard utilization ratio. See `paper/WHITEPAPER.md`, section 2.

## Quick start

Requires Python 3.10+. No dependencies, no network.

```sh
sh run.sh
```

Verify file integrity (optional):

```sh
sha256sum -c MANIFEST.sha256
```

## Solidity parity (not yet verified)

The Solidity mirror was **not executed when this capsule was built**. To check parity yourself, install [Foundry](https://book.getfoundry.sh/) and forge-std, then run:

```sh
forge test -vv
```

## Layout

| Path | Contents |
|---|---|
| `ledger/` | Hash-chained Cognitive State Ledger |
| `ref/` | Canonical Python model |
| `src/` | Solidity mirror (`CreditAuditSM.sol`) |
| `tests/` | Test vectors, test suite, mutation tester, Foundry test generator |
| `test/` | Generated Foundry parity test |
| `paper/` | White paper (`WHITEPAPER.md`) |
| `MANIFEST.sha256` | SHA-256 hashes of capsule files |

## Expected output

`<paste the final lines of a clean run, including the top-level hash>`

## Reproducibility scope

- Arithmetic is integer-only, so results do not depend on floating-point behavior.
- Verified on: `<Python version, OS, architecture>`. Results on other platforms are unconfirmed until tested.
- Mutation testing: `<operator set, mutants generated, killed, survivors, excluded equivalents>`

## Limitations

- Research artifact. Not a consumer credit score, and not for lending, underwriting, or adverse-action decisions.
- Does not reproduce any bureau or vendor scoring model.
- Solidity parity is unverified until you run the Foundry tests.

## License

`<license>`
