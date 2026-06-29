import pytest
import sys
from pathlib import Path

# Adjust path to import app module
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent import get_compliance_workflow, GraphState

def test_happy_path_ledger_approval():
    """Verify that a standard transaction under $10,000 is automatically approved."""
    payload = {
        "invoice_id": "INV-1001",
        "vendor_name": "ACME Supplies Ltd.",
        "amount": 1500.00
    }
    workflow = get_compliance_workflow()
    state = GraphState(raw_payload=payload)
    
    result = workflow.run(state)
    
    assert result.status == "LEDGER_APPROVED"
    assert result.directive == "PROCEED"
    assert result.invoice_id == "INV-1001"
    assert result.vendor_name == "ACME Supplies Ltd."
    assert result.amount == 1500.00
    assert any("Passed. Amount $1500.00" in log for log in result.logs)
    assert any("Automation Proceeding" in log for log in result.logs)

def test_anomalous_boundary_triage_suspension():
    """Verify that a transaction exceeding $10,000 is flagged and suspends downstream automation."""
    payload = {
        "invoice_id": "INV-9999",
        "vendor_name": "Globex Corp",
        "amount": 25000.00
    }
    workflow = get_compliance_workflow()
    state = GraphState(raw_payload=payload)
    
    result = workflow.run(state)
    
    assert result.status == "FLAGGED_FOR_TRIAGE"
    assert result.directive == "SUSPEND_AUTOMATION"
    assert result.invoice_id == "INV-9999"
    assert result.vendor_name == "Globex Corp"
    assert result.amount == 25000.00
    assert any("Flagged. Amount $25000.00" in log for log in result.logs)
    assert any("Automation Suspended" in log for log in result.logs)

def test_exact_boundary_threshold():
    """Verify that a transaction exactly at $10,000 is approved (boundary check)."""
    payload = {
        "invoice_id": "INV-10000",
        "vendor_name": "Boundary Testing",
        "amount": 10000.00
    }
    workflow = get_compliance_workflow()
    state = GraphState(raw_payload=payload)
    
    result = workflow.run(state)
    
    assert result.status == "LEDGER_APPROVED"
    assert result.directive == "PROCEED"

def test_extraction_missing_fields():
    """Verify handling of payloads missing required fields."""
    payload = {
        "invoice_id": "INV-ERR",
        "vendor_name": "Incomplete Inc."
        # Missing amount
    }
    workflow = get_compliance_workflow()
    state = GraphState(raw_payload=payload)
    
    result = workflow.run(state)
    
    assert result.status == "ERROR"
    assert result.directive == "SUSPEND_AUTOMATION"
    assert any("Missing amount in payload" in log for log in result.logs)

def test_extraction_invalid_amount_type():
    """Verify handling of payloads with invalid amount types."""
    payload = {
        "invoice_id": "INV-ERR-2",
        "vendor_name": "Bad Data Corp",
        "amount": "NOT_A_NUMBER"
    }
    workflow = get_compliance_workflow()
    state = GraphState(raw_payload=payload)
    
    result = workflow.run(state)
    
    assert result.status == "ERROR"
    assert result.directive == "SUSPEND_AUTOMATION"
    assert any("Invalid amount format" in log for log in result.logs)
