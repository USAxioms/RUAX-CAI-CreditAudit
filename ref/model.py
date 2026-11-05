"""WAD18 Credit Audit State Machine: canonical integer-only reference. No floats. Total functions."""
import hashlib

WAD = 10**18
INPUT_CAP = 10**30
W_PAYMENT = 350000000000000000
W_OWED = 300000000000000000
W_LENGTH = 150000000000000000
W_NEW = 100000000000000000
W_MIX = 100000000000000000
COLLECTION_PENALTY = 100000000000000000
COLLECTION_CAP = 4
AGE_CAP_MONTHS = 240
INQUIRY_CAP = 6
TYPE_CAP = 4
SCORE_FLOOR = 300
SCORE_SPAN = 550
GENESIS = bytes(32)

FIELDS = ("on_time", "total", "collections", "balance", "limit", "age_months", "inquiries", "types")


def mn(a, b):
    return a if a < b else b


def wmul(a, b):
    return (a * b) // WAD


def wdiv(a, b):
    if b == 0:
        return 0
    return (a * WAD) // b


def clamp_inputs(inp):
    return tuple(mn(max(v, 0), INPUT_CAP) for v in inp)


def payment_sub(on_time, total, collections):
    base = wdiv(mn(on_time, total), total)
    penalty = mn(collections, COLLECTION_CAP) * COLLECTION_PENALTY
    return wmul(base, WAD - penalty)


def utilization(balance, limit):
    if limit == 0:
        if balance > 0:
            return WAD
        return 0
    return mn(wdiv(balance, limit), WAD)


def owed_sub(balance, limit):
    return WAD - utilization(balance, limit)


def length_sub(age_months):
    return wdiv(mn(age_months, AGE_CAP_MONTHS), AGE_CAP_MONTHS)


def new_sub(inquiries):
    return WAD - wdiv(mn(inquiries, INQUIRY_CAP), INQUIRY_CAP)


def mix_sub(types):
    return wdiv(mn(types, TYPE_CAP), TYPE_CAP)


def composite(sp, so, sl, sn, sm):
    return (wmul(W_PAYMENT, sp) + wmul(W_OWED, so) + wmul(W_LENGTH, sl)
            + wmul(W_NEW, sn) + wmul(W_MIX, sm))


def to_score(comp):
    return SCORE_FLOOR + (SCORE_SPAN * comp) // WAD


def audit(inp):
    """Pure function: raw integer inputs -> full transparent trace."""
    on_time, total, coll, bal, lim, age, inq, typ = clamp_inputs(inp)
    sp = payment_sub(on_time, total, coll)
    so = owed_sub(bal, lim)
    sl = length_sub(age)
    sn = new_sub(inq)
    sm = mix_sub(typ)
    comp = composite(sp, so, sl, sn, sm)
    return {"utilization": utilization(bal, lim), "payment": sp, "owed": so, "length": sl,
            "new": sn, "mix": sm, "composite": comp, "score": to_score(comp)}


def _b32(v):
    return v.to_bytes(32, "big")


def next_state(prev_hash, nonce, inp, trace):
    clamped = clamp_inputs(inp)
    data = prev_hash + _b32(nonce)
    for v in clamped:
        data += _b32(v)
    for k in ("payment", "owed", "length", "new", "mix", "composite", "score"):
        data += _b32(trace[k])
    return hashlib.sha256(data).digest()


def run(inputs_seq):
    """State machine: fold a sequence of input tuples; returns list of (trace, state_hash_hex)."""
    h = GENESIS
    out = []
    n = 0
    for inp in inputs_seq:
        t = audit(inp)
        h = next_state(h, n, inp, t)
        out.append((t, h.hex()))
        n += 1
    return out
