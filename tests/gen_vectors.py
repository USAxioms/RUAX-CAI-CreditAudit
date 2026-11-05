"""Deterministic vector generation: integer LCG only (no random module, no floats)."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ref"))
import model

EDGE = [
    (95, 100, 0, 3000, 10000, 120, 2, 3),   # golden anchor
    (0, 0, 0, 0, 0, 0, 0, 0),               # all zero
    (0, 0, 0, 500, 0, 0, 0, 0),             # limit 0, balance > 0
    (0, 0, 0, 1, 0, 0, 0, 0),               # limit 0, balance exactly 1 (boundary)
    (10, 10, 0, 0, 0, 240, 0, 4),           # limit 0, balance 0, perfect-ish
    (10, 10, 0, 20000, 10000, 300, 9, 7),   # util > 1, caps exceeded
    (5, 10, 4, 5000, 10000, 12, 6, 2),      # collections at cap, inquiries at cap
    (5, 10, 9, 5000, 10000, 239, 5, 3),     # collections above cap
    (12, 10, 0, 1, 10000, 241, 7, 5),       # on_time > total
    (10, 10, 1, 9999, 10000, 1, 1, 1),
    (1, 3, 0, 1, 3, 7, 1, 1),               # non-terminating divisions
    (2, 3, 2, 2, 3, 100, 4, 3),
    (10**31, 10**31, 10**31, 10**31, 10**31, 10**31, 10**31, 10**31),  # cap overflow guard
    (7, 7, 0, 10**30, 10**30, 240, 0, 4),   # exactly at cap
]

def lcg(seed):
    x = seed
    while True:
        x = (x * 6364136223846793005 + 1442695040888963407) % (2**64)
        yield x >> 33

def generate(n=240):
    g = lcg(20261104)
    rows = list(EDGE)
    for _ in range(n):
        total = next(g) % 400
        on = next(g) % (total + 3)
        lim = next(g) % 2000000
        bal = next(g) % (lim * 2 + 5)
        rows.append((on, total, next(g) % 7, bal, lim, next(g) % 400, next(g) % 10, next(g) % 7))
    return rows

if __name__ == "__main__":
    rows = generate()
    res = model.run(rows)
    out = [{"inputs": list(r), "trace": t, "state_hash": h} for r, (t, h) in zip(rows, res)]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectors.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print("vectors", len(out), "final", out[-1]["state_hash"])
