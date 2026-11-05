"""Generates test/Parity.t.sol from vectors.json so the Solidity contract can be checked bit-for-bit with Foundry."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
vecs = json.load(open(os.path.join(HERE, "vectors.json")))
CH = 40
out = ['// SPDX-License-Identifier: MIT', 'pragma solidity ^0.8.20;',
 'import "forge-std/Test.sol";', 'import "../src/CreditAuditSM.sol";',
 'contract ParityTest is Test {', '  CreditAuditSM sm;',
 '  struct Exp { uint256 u; uint256 p; uint256 o; uint256 l; uint256 n; uint256 m; uint256 c; uint256 s; bytes32 h; }',
 '  function setUp() public { sm = new CreditAuditSM(); }',
 '  function _chk(CreditAuditSM.Inputs memory i, Exp memory e) internal {',
 '    CreditAuditSM.Trace memory t = sm.submit(i);',
 '    assertEq(t.utilization, e.u); assertEq(t.payment, e.p); assertEq(t.owed, e.o);',
 '    assertEq(t.length, e.l); assertEq(t.newCredit, e.n); assertEq(t.mix, e.m);',
 '    assertEq(t.composite, e.c); assertEq(t.score, e.s); assertEq(sm.stateHash(), e.h);',
 '  }']
# Single ordered test (state hash chain requires sequential submits from genesis)
for k in range(0, len(vecs), CH):
    out.append('  function _part%d() internal {' % (k // CH))
    for v in vecs[k:k + CH]:
        i, t = v["inputs"], v["trace"]
        out.append('    _chk(CreditAuditSM.Inputs(%s), Exp(%d,%d,%d,%d,%d,%d,%d,%d,bytes32(0x%s)));' % (
            ",".join(str(x) for x in i), t["utilization"], t["payment"], t["owed"], t["length"],
            t["new"], t["mix"], t["composite"], t["score"], v["state_hash"]))
    out.append('  }')
out.append('  function testParityAll() public {')
for k in range(0, len(vecs), CH):
    out.append('    _part%d();' % (k // CH))
out.append('  }')
out.append('}')
os.makedirs(os.path.join(HERE, "..", "test"), exist_ok=True)
open(os.path.join(HERE, "..", "test", "Parity.t.sol"), "w").write("\n".join(out) + "\n")
print("foundry test generated", len(vecs))
