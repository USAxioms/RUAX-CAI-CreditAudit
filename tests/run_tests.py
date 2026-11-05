import sys, os, types
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import suite
src = open(os.path.join(HERE, "..", "ref", "model.py")).read()
m = types.ModuleType("model"); exec(compile(src, "model.py", "exec"), m.__dict__)
fails = suite.run_suite(m, src)
print("BASE_SUITE", "PASS" if not fails else "FAIL %s" % fails[:5])
sys.exit(1 if fails else 0)
