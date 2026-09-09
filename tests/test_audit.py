from src.mcpbridge.audit import (
    append_audit,
    list_audit,
    reset_audit_for_tests,
    verify_audit_chain,
)


def _append(index: int):
    return append_audit(
        actor=f"actor-{index}",
        role="operator",
        phase="executed",
        server="business",
        tool="generate_decision_pack",
        decision="auto-read",
        arguments={"index": index},
    )


def test_audit_chain_links_and_verifies_events():
    reset_audit_for_tests()
    first = append_audit(
        actor="a",
        role="operator",
        phase="proposed",
        server="itsm",
        tool="create_incident",
        decision="approval_required",
        arguments={"x": 1},
    )
    second = append_audit(
        actor="b",
        role="approver",
        phase="executed",
        server="itsm",
        tool="create_incident",
        decision="approve",
        arguments={"x": 1},
    )
    assert second.previous_hash == first.event_hash
    assert len(list_audit()) == 2
    assert verify_audit_chain() is True


def test_audit_chain_remains_valid_after_bounded_buffer_rollover():
    reset_audit_for_tests()
    for index in range(275):
        _append(index)

    # The in-memory retention boundary is 250 events. Integrity verification must continue
    # from the retained anchor rather than incorrectly expecting GENESIS after old events roll off.
    assert len(list_audit(1000)) == 100
    assert verify_audit_chain() is True
