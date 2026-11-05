"""Verification suite. run_suite(module, source) -> list of failure strings (empty = pass)."""
import ast, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ANCHOR_IN = (95, 100, 0, 3000, 10000, 120, 2, 3)
ANCHOR_OUT = {"utilization": 300000000000000000, "payment": 950000000000000000,
              "owed": 700000000000000000, "length": 500000000000000000,
              "new": 666666666666666667, "mix": 750000000000000000,
              "composite": 759166666666666666, "score": 717}

def lint(source):
    bad = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            bad.append("float literal")
        if isinstance(node, ast.Div):
            bad.append("true division")
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "float":
            bad.append("float() call")
        if isinstance(node, (ast.Raise, ast.Assert)):
            bad.append("exception/assert in total function")
    return bad

def run_suite(m, source):
    f = []
    f += ["LINT:" + b for b in lint(source)]
    try:
        if m.audit(ANCHOR_IN) != ANCHOR_OUT:
            f.append("ANCHOR")
        if m.W_PAYMENT + m.W_OWED + m.W_LENGTH + m.W_NEW + m.W_MIX != m.WAD:
            f.append("WEIGHTS_SUM")
        if (m.W_PAYMENT, m.W_OWED, m.W_LENGTH, m.W_NEW, m.W_MIX) != (35 * 10**16, 30 * 10**16, 15 * 10**16, 10**17, 10**17):
            f.append("WEIGHTS_PUBLISHED")
        vecs = json.load(open(os.path.join(HERE, "vectors.json")))
        res = m.run([tuple(v["inputs"]) for v in vecs])
        for i, (v, (t, h)) in enumerate(zip(vecs, res)):
            if t != v["trace"]:
                f.append("TRACE@%d" % i)
            if h != v["state_hash"]:
                f.append("HASH@%d" % i)
        # totality & range properties
        for v in vecs:
            t = m.audit(tuple(v["inputs"]))
            if not (300 <= t["score"] <= 850):
                f.append("SCORE_RANGE")
            for k in ("payment", "owed", "length", "new", "mix", "utilization"):
                if not (0 <= t[k] <= m.WAD):
                    f.append("SUB_RANGE:" + k)
        # monotonicity: more collections never raises payment sub-score
        a = m.audit((8, 10, 0, 1, 10, 50, 1, 2))["payment"]
        b = m.audit((8, 10, 1, 1, 10, 50, 1, 2))["payment"]
        if not b < a:
            f.append("MONO_COLLECTIONS")
        # negative inputs clamp to zero
        if m.clamp_inputs((-5, 3)) != (0, 3):
            f.append("CLAMP_NEG")
        if m.clamp_inputs((10**31,)) != (10**30,):
            f.append("CLAMP_CAP")
    except Exception as e:  # a mutant that crashes is killed; reference must never crash
        f.append("EXC:" + type(e).__name__)
    return f
