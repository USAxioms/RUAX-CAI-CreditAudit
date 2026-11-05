# WAD18 Credit Audit State Machine: Reproducibility Capsule v0.1.0

Deterministic, integer-only (1e18 fixed point) credit-report audit state machine. Python is the canonical reference;
`src/CreditAuditSM.sol` mirrors it. Every run prints its full intermediate math (the Trace).

Run (Python 3.10+, no dependencies, no network): `sh run.sh`
Solidity parity (user must run; NOT executed when this capsule was built): install Foundry + forge-std, then `forge test -vv`.

Layout: ledger/ (hash-chained Cognitive State Ledger), ref/ (canonical model), src/ (Solidity), tests/ (vectors, suite,
mutation tester, Foundry generator), test/ (generated Foundry parity test), paper/ (white paper), MANIFEST.sha256.

IMPORTANT: this is NOT the FICO or VantageScore algorithm (those are proprietary and unpublished). It mirrors only the
publicly documented factor weights (35/30/15/10/10) and the standard utilization ratio. See paper/WHITEPAPER.md section 2.
