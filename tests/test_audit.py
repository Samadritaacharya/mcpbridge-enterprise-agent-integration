from src.mcpbridge.audit import (
    append_audit,
    list_audit,
    reset_audit_for_tests,
    verify_audit_chain,
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
