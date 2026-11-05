# A WAD18 Deterministic State Machine for Transparent Credit Report Auditing
Capsule v0.1.0 · 2026-11-04 · Part of a human-guided, blockchain-native safe-AI initiative

## Abstract
We specify and implement a deterministic state machine that maps credit-report inputs to a score using only 18-decimal
integer fixed-point arithmetic (WAD18). Every run emits its complete intermediate math, and every state transition is
hash-chained. The same logic is implemented in a canonical Python reference and a Solidity contract; a reproducibility
capsule ships golden vectors, a mutation-testing harness, and an append-only Cognitive State Ledger.

## 1. Axioms
A1. Arithmetic is exact integer arithmetic. Value x is represented as X = x·10^18 (WAD). No floating point anywhere
(enforced by an AST lint in the test suite: no float literals, no true division, no float()).
A2. All functions are total: no division by zero, no revert, no exception. Zero denominators return a defined value.
A3. Division is floor division on non-negative integers; multiplication of WADs is floor(a·b / 10^18).
A4. Execution is bit-for-bit reproducible across environments (integer semantics are platform-independent).

## 2. What is and is not mirrored (honest scope)
Credit bureaus and score developers do not publish exact scoring formulas. What is publicly documented, and mirrored here:
- FICO category weights: payment history 35%, amounts owed 30%, length of history 15%, new credit 10%, credit mix 10%
  (published by Experian, Freddie Mac, American Express educational pages).
- Credit utilization = revolving balances / revolving limits (the "amounts owed" driver).
- Score range 300–850.
Not mirrored, because not public: the proprietary sub-score functions, point tables, and score-card segmentation.
VantageScore uses different weights (payment history about 40–41%) and is not implemented in v0.1.0.
Therefore the sub-score rules in §3 are explicit, open, auditable **assumptions** designed for transparency; this model
is a standard-setting audit reference, **not** a reproduction of any bureau or FICO score.

## 3. Model
Inputs (non-negative integers, clamped to ≤10^30): on_time, total (payments), collections, balance, limit (cents),
age_months, inquiries, types. Let min(a,b) be the integer minimum.
- payment: base = wdiv(min(on_time,total), total); penalty = min(collections,4)·0.10·WAD; S_pay = wmul(base, WAD − penalty)
- utilization u = WAD if limit=0 and balance>0; 0 if limit=0 and balance=0; else min(wdiv(balance,limit), WAD). S_owed = WAD − u
- S_len = wdiv(min(age_months,240), 240)
- S_new = WAD − wdiv(min(inquiries,6), 6)
- S_mix = wdiv(min(types,4), 4)
- C = Σ wmul(w_k, S_k) with w = (0.35, 0.30, 0.15, 0.10, 0.10) in WAD
- Score = 300 + floor(550·C / WAD)

Worked anchor (hand-verified): on_time 95/100, collections 0, balance 3000 / limit 10000, 120 months, 2 inquiries, 3 types
gives S = (0.95, 0.70, 0.50, 0.666666666666666667, 0.75), C = 759166666666666666, Score = 717.

## 4. State machine
State σ_n = (h_n, n). Transition: h_{n+1} = SHA-256(h_n ‖ n ‖ clamped inputs ‖ S_pay ‖ S_owed ‖ S_len ‖ S_new ‖ S_mix ‖ C ‖ Score),
each field as a 32-byte big-endian word; h_0 = 32 zero bytes. This equals abi.encodePacked of uint256 values in Solidity,
so the on-chain `stateHash` must equal the Python chain hash for the same input sequence.

## 5. Theorems
T1 (Totality). Every function terminates with a value for every input. Proof: the only division is wdiv, which guards b=0;
utilization guards limit=0; no loops with data-dependent bounds exist; inputs are clamped so no operand is negative.
T2 (Range). Each S_k ∈ [0, WAD], C ∈ [0, WAD], Score ∈ [300, 850]. Proof: min-caps bound each ratio by WAD; penalty ≤ 0.4·WAD so
WAD − penalty ≥ 0; the weights sum to WAD, so C ≤ Σ w_k·WAD/WAD = WAD; floor preserves bounds.
T3 (No overflow in Solidity). Clamped inputs ≤ 10^30; the largest product is a·WAD ≤ 10^48 < 2^256 ≈ 1.16·10^77; 550·C ≤ 5.5·10^20; collection penalty ≤ 4·10^17.
T4 (Rounding bound). Every floor loses less than 1 ulp (10^-18). S_pay has two floors (<2 ulp), the other sub-scores at most one (<1 ulp); weights are exact and sum to 1, so sub-score error contributes <2 ulp to C, and the five wmul floors add <5 ulp. Hence |C − C_exact| < 7 ulp, and the final Score truncation adds <1 point.
T5 (Monotonicity). More collections never raises S_pay (tested; follows from penalty being non-decreasing and wmul monotone).
T6 (Determinism). A1–A3 and integer semantics imply identical outputs on any conforming Python or EVM implementation; SHA-256 is standardized.

## 6. Verification evidence (executed in the build sandbox)
- 254 golden vectors (13 hand-chosen boundary cases + LCG-generated cases; integer-only generator): reference passes.
- Mutation testing: every operator and integer literal of ref/model.py mutated once (50 mutants). 49 non-equivalent mutants,
  49 killed (1000 permille). One mutant (`<` → `<=` in `mn`) is provably equivalent: min(a,b) returns the same value when a=b.
  The first run killed 48/50 and exposed a real coverage gap (limit=0, balance=1); a boundary vector was added and logged in the ledger.
- Ledger hash chain verifies.

## 7. Not yet verified: stated plainly
- Solidity was NOT compiled or executed in the build sandbox (no solc/Foundry, no network). Bit-for-bit Solidity parity is
  therefore **unproven until `forge test` passes** on test/Parity.t.sol, which checks all 254 vectors and the chained state hash.
- Mutation testing covers the Python reference only. Run a Solidity mutation tool (e.g. Gambit) after parity passes.
- The model has not been validated against real bureau data or reviewed for FCRA/ECOA compliance, and must not be used to make credit decisions without that review.

## 8. Roadmap
(1) Run Foundry parity. (2) Choose target score model (FICO vs VantageScore, version) and replace assumption sub-scores with published rules where documented. (3) Metro 2 input mapping. (4) Solidity mutation suite. (5) Independent audit.

## 9. Sources (public)
Experian "What Affects Your Credit Scores?"; Freddie Mac "The 5 Factors that Make Up Your Credit Score"; American Express "How Is a Credit Score Calculated?".
