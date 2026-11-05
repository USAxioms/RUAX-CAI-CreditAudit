"""Token-level mutation tester: mutates every operator and integer literal of ref/model.py once."""
import sys, os, io, tokenize, types, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import suite
EQUIVALENT = {(24, "<", "<=")}  # mn(a,b): a<=b vs a<b yields same value when a==b
SRC = open(os.path.join(HERE, "..", "ref", "model.py")).read()
OPS = {"+": ["-"], "-": ["+"], "*": ["+"], "//": ["*"], "<": [">", "<="], ">": ["<", ">="],
       "==": ["!="], "**": ["*"]}

def offsets(src):
    starts, pos = [0], 0
    for line in src.splitlines(keepends=True):
        pos += len(line); starts.append(pos)
    return starts

def mutants(src):
    st = offsets(src)
    out = []
    for t in tokenize.generate_tokens(io.StringIO(src).readline):
        a = st[t.start[0] - 1] + t.start[1]
        b = st[t.end[0] - 1] + t.end[1]
        if t.type == tokenize.OP and t.string in OPS:
            for r in OPS[t.string]:
                out.append((t.start[0], t.string, r, src[:a] + r + src[b:]))
        elif t.type == tokenize.NUMBER and t.string.isdigit():
            for r in (str(int(t.string) + 1),):
                out.append((t.start[0], t.string, r, src[:a] + r + src[b:]))
    return out

def main():
    killed = survived = invalid = equiv = 0
    survivors = []
    for line, old, new, msrc in mutants(SRC):
        try:
            code = compile(msrc, "mutant", "exec")
        except SyntaxError:
            invalid += 1; continue
        m = types.ModuleType("mut")
        try:
            exec(code, m.__dict__)
            fails = suite.run_suite(m, msrc)
        except Exception:
            fails = ["LOAD_EXC"]
        if (line, old, new) in EQUIVALENT:
            equiv += 1
        elif fails:
            killed += 1
        else:
            survived += 1; survivors.append((line, old, new))
    total = killed + survived
    print("MUTANTS non_equivalent=%d killed=%d survived=%d proven_equivalent_excluded=%d invalid_skipped=%d" % (total, killed, survived, equiv, invalid))
    for s in survivors:
        print("SURVIVOR line %d: %s -> %s" % s)
    # integer permille score (no floats)
    print("MUTATION_SCORE_PERMILLE", (killed * 1000) // total if total else 0)
    json.dump({"total": total, "killed": killed, "survived": survived, "survivors": survivors},
              open(os.path.join(HERE, "mutant_report.json"), "w"), indent=1)
    return survived

if __name__ == "__main__":
    sys.exit(1 if main() else 0)
