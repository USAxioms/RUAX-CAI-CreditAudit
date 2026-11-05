// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title WAD18 Credit Audit State Machine (mirror of ref/model.py)
/// @notice Integer-only, 1e18 fixed point. No floats. No reverts in audit(): all functions total.
library WAD18 {
    uint256 internal constant WAD = 1e18;
    uint256 internal constant INPUT_CAP = 1e30;

    function mn(uint256 a, uint256 b) internal pure returns (uint256) { return a < b ? a : b; }
    function wmul(uint256 a, uint256 b) internal pure returns (uint256) { return (a * b) / WAD; }
    function wdiv(uint256 a, uint256 b) internal pure returns (uint256) {
        if (b == 0) return 0;
        return (a * WAD) / b;
    }
}

contract CreditAuditSM {
    using WAD18 for uint256;

    uint256 internal constant WAD = 1e18;
    uint256 internal constant INPUT_CAP = 1e30;
    uint256 internal constant W_PAYMENT = 350000000000000000;
    uint256 internal constant W_OWED = 300000000000000000;
    uint256 internal constant W_LENGTH = 150000000000000000;
    uint256 internal constant W_NEW = 100000000000000000;
    uint256 internal constant W_MIX = 100000000000000000;
    uint256 internal constant COLLECTION_PENALTY = 100000000000000000;
    uint256 internal constant COLLECTION_CAP = 4;
    uint256 internal constant AGE_CAP_MONTHS = 240;
    uint256 internal constant INQUIRY_CAP = 6;
    uint256 internal constant TYPE_CAP = 4;
    uint256 internal constant SCORE_FLOOR = 300;
    uint256 internal constant SCORE_SPAN = 550;

    struct Inputs {
        uint256 onTime; uint256 total; uint256 collections; uint256 balance;
        uint256 limit; uint256 ageMonths; uint256 inquiries; uint256 types;
    }
    struct Trace {
        uint256 utilization; uint256 payment; uint256 owed; uint256 length;
        uint256 newCredit; uint256 mix; uint256 composite; uint256 score;
    }

    bytes32 public stateHash;
    uint256 public nonce;

    event Audited(uint256 indexed nonce, bytes32 stateHash, uint256 composite, uint256 score);

    function _utilization(uint256 bal, uint256 lim) internal pure returns (uint256) {
        if (lim == 0) return bal > 0 ? WAD : 0;
        return WAD18.mn(WAD18.wdiv(bal, lim), WAD);
    }

    function _clamp(Inputs memory i) internal pure returns (Inputs memory) {
        i.onTime = WAD18.mn(i.onTime, INPUT_CAP);
        i.total = WAD18.mn(i.total, INPUT_CAP);
        i.collections = WAD18.mn(i.collections, INPUT_CAP);
        i.balance = WAD18.mn(i.balance, INPUT_CAP);
        i.limit = WAD18.mn(i.limit, INPUT_CAP);
        i.ageMonths = WAD18.mn(i.ageMonths, INPUT_CAP);
        i.inquiries = WAD18.mn(i.inquiries, INPUT_CAP);
        i.types = WAD18.mn(i.types, INPUT_CAP);
        return i;
    }

    function audit(Inputs memory raw) public pure returns (Trace memory t) {
        Inputs memory i = _clamp(raw);
        uint256 base = WAD18.wdiv(WAD18.mn(i.onTime, i.total), i.total);
        uint256 penalty = WAD18.mn(i.collections, COLLECTION_CAP) * COLLECTION_PENALTY;
        t.payment = WAD18.wmul(base, WAD - penalty);
        t.utilization = _utilization(i.balance, i.limit);
        t.owed = WAD - t.utilization;
        t.length = WAD18.wdiv(WAD18.mn(i.ageMonths, AGE_CAP_MONTHS), AGE_CAP_MONTHS);
        t.newCredit = WAD - WAD18.wdiv(WAD18.mn(i.inquiries, INQUIRY_CAP), INQUIRY_CAP);
        t.mix = WAD18.wdiv(WAD18.mn(i.types, TYPE_CAP), TYPE_CAP);
        t.composite = WAD18.wmul(W_PAYMENT, t.payment) + WAD18.wmul(W_OWED, t.owed)
            + WAD18.wmul(W_LENGTH, t.length) + WAD18.wmul(W_NEW, t.newCredit)
            + WAD18.wmul(W_MIX, t.mix);
        t.score = SCORE_FLOOR + (SCORE_SPAN * t.composite) / WAD;
    }

    function submit(Inputs memory raw) external returns (Trace memory t) {
        t = audit(raw);
        Inputs memory i = _clamp(raw);
        stateHash = sha256(abi.encodePacked(
            stateHash, nonce,
            i.onTime, i.total, i.collections, i.balance, i.limit, i.ageMonths, i.inquiries, i.types,
            t.payment, t.owed, t.length, t.newCredit, t.mix, t.composite, t.score));
        emit Audited(nonce, stateHash, t.composite, t.score);
        nonce += 1;
    }
}
