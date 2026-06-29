import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("compliance_triage")

@dataclass
class GraphState:
    raw_payload: Dict[str, Any]
    invoice_id: Optional[str] = None
    vendor_name: Optional[str] = None
    amount: float = 0.0
    status: str = "PENDING"  # PENDING, FLAGGED_FOR_TRIAGE, LEDGER_APPROVED, ERROR
    directive: str = "PROCEED"  # PROCEED, SUSPEND_AUTOMATION
    logs: List[str] = field(default_factory=list)

class ExtractionNode:
    def execute(self, state: GraphState) -> GraphState:
        """Parses incoming JSON dictionaries (invoice_id/id, vendor_name/vendor, amount)."""
        payload = state.raw_payload
        state.logs.append("ExtractionNode: Parsing incoming invoice payload.")
        
        try:
            invoice_id = payload.get("invoice_id") or payload.get("id")
            vendor_name = payload.get("vendor_name") or payload.get("vendor")
            amount_raw = payload.get("amount")
            
            if not invoice_id:
                raise ValueError("Missing invoice_id in payload.")
            if not vendor_name:
                raise ValueError("Missing vendor_name in payload.")
            if amount_raw is None:
                raise ValueError("Missing amount in payload.")
                
            try:
                amount = float(amount_raw)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid amount format: {amount_raw}")
                
            state.invoice_id = str(invoice_id)
            state.vendor_name = str(vendor_name)
            state.amount = amount
            state.logs.append(
                f"ExtractionNode: Successfully parsed invoice {invoice_id} "
                f"from {vendor_name} for amount ${amount:.2f}."
            )
        except Exception as e:
            state.status = "ERROR"
            state.directive = "SUSPEND_AUTOMATION"
            state.logs.append(f"ExtractionNode Error: {str(e)}")
            logger.error(f"Extraction Node error: {e}")
            
        return state

class PolicyValidationNode:
    THRESHOLD = 10000.00
    
    def execute(self, state: GraphState) -> GraphState:
        """References compliance threshold rules to flag or pass transactions."""
        if state.status == "ERROR":
            state.logs.append("PolicyValidationNode: Skipping due to upstream extraction error.")
            return state
            
        state.logs.append("PolicyValidationNode: Checking transaction compliance threshold.")
        
        # Rule: Any financial payload amount exceeding $10,000 must immediately be flagged for manual human triage
        if state.amount > self.THRESHOLD:
            state.status = "FLAGGED_FOR_TRIAGE"
            state.logs.append(
                f"PolicyValidationNode: Flagged. Amount ${state.amount:.2f} "
                f"exceeds the compliance threshold limit of ${self.THRESHOLD:.2f}."
            )
        else:
            state.status = "LEDGER_APPROVED"
            state.logs.append(
                f"PolicyValidationNode: Passed. Amount ${state.amount:.2f} "
                f"is within the compliance threshold limit of ${self.THRESHOLD:.2f}."
            )
            
        return state

class TriageRoutingNode:
    def execute(self, state: GraphState) -> GraphState:
        """Implements an ironclad Human-in-the-Loop execution gate.
        
        If a transaction status is FLAGGED_FOR_TRIAGE, returns a SUSPEND_AUTOMATION directive.
        """
        state.logs.append("TriageRoutingNode: Evaluating workflow status and routing.")
        
        if state.status == "FLAGGED_FOR_TRIAGE":
            state.directive = "SUSPEND_AUTOMATION"
            state.logs.append(
                "TriageRoutingNode: [ALERT] Automation Suspended. "
                "Halting downstream database operations. Manual administrative approval required."
            )
        elif state.status == "LEDGER_APPROVED":
            state.directive = "PROCEED"
            state.logs.append(
                "TriageRoutingNode: Automation Proceeding. Transaction cleared for automatic ledger writing."
            )
        else:
            state.directive = "SUSPEND_AUTOMATION"
            state.logs.append(
                "TriageRoutingNode: Anomalous workflow state detected. Suspending automation for security."
            )
            
        return state

# ADK 2.0 compatible classes
class Agent:
    def __init__(self, name: str, instruction: str):
        self.name = name
        self.instruction = instruction

class Workflow:
    def __init__(self, name: str, edges: List[Tuple[Any, Any] | Tuple[Any, Any, Any]]):
        self.name = name
        self.edges = edges
        
    def run(self, initial_state: GraphState) -> GraphState:
        """Executes the workflow graph sequentially from START through each node."""
        current_state = initial_state
        
        # Instantiate execution nodes
        extraction = ExtractionNode()
        validation = PolicyValidationNode()
        triage = TriageRoutingNode()
        
        # Sequentially execute the nodes as defined by the graph edges
        current_state = extraction.execute(current_state)
        current_state = validation.execute(current_state)
        current_state = triage.execute(current_state)
        
        return current_state

def get_compliance_workflow() -> Workflow:
    """Returns the orchestrator graph workflow."""
    return Workflow(
        name="automated_finance_triage_workflow",
        edges=[
            ("START", ExtractionNode),
            (ExtractionNode, PolicyValidationNode),
            (PolicyValidationNode, TriageRoutingNode)
        ]
    )

def run_triage_pipeline(incoming_data: Dict[str, Any]) -> Dict[str, Any]:
    """Runs the compliance triage pipeline for the incoming data using the Graph Workflow."""
    workflow = get_compliance_workflow()
    state = GraphState(raw_payload=incoming_data)
    result_state = workflow.run(state)
    
    if result_state.status == "LEDGER_APPROVED":
        action = "COMMIT_TO_LEDGER"
        compliance_status = "APPROVED"
        message = f"SUCCESS: Invoice {result_state.invoice_id} approved automatically."
        failure_reason = ""
    elif result_state.status == "FLAGGED_FOR_TRIAGE":
        action = "SUSPEND_AUTOMATION"
        compliance_status = "FLAGGED_FOR_TRIAGE"
        failure_reason = f"Transaction exceeds standard threshold limit of $10000.0."
        message = f"ALERT: Manual review needed for Invoice {result_state.invoice_id}. Reason: {failure_reason}"
    elif result_state.status == "ERROR":
        action = "SUSPEND_AUTOMATION"
        compliance_status = "REJECTED"
        # Extract parsing error message from logs
        err_msg = "Extraction error encountered."
        for log in reversed(result_state.logs):
            if "ExtractionNode Error:" in log:
                err_msg = log.split("ExtractionNode Error:", 1)[1].strip()
                break
        failure_reason = err_msg
        message = f"REJECTED: {failure_reason}"
    else:
        action = "SUSPEND_AUTOMATION"
        compliance_status = "REJECTED"
        failure_reason = "Anomalous workflow state detected."
        message = f"REJECTED: {failure_reason}"
        
    return {
        "action": action,
        "message": message,
        "payload": {
            "invoice_id": result_state.invoice_id or "UNKNOWN",
            "vendor_name": result_state.vendor_name or "UNKNOWN",
            "amount": result_state.amount,
            "compliance_status": compliance_status,
            "failure_reason": failure_reason
        }
    }

if __name__ == "__main__":
    # Example execution run
    workflow = get_compliance_workflow()
    
    # Test high amount (should suspend)
    payload_high = {"invoice_id": "INV-001", "vendor_name": "MegaCorp", "amount": 15000.00}
    state_high = GraphState(raw_payload=payload_high)
    result_high = workflow.run(state_high)
    print(f"\n--- Test High Amount ($15,000) ---")
    print(f"Status: {result_high.status}")
    print(f"Directive: {result_high.directive}")
    print("Logs:")
    for log in result_high.logs:
        print(f"  - {log}")
        
    # Test low amount (should approve)
    payload_low = {"invoice_id": "INV-002", "vendor_name": "MicroCorp", "amount": 450.00}
    state_low = GraphState(raw_payload=payload_low)
    result_low = workflow.run(state_low)
    print(f"\n--- Test Low Amount ($450) ---")
    print(f"Status: {result_low.status}")
    print(f"Directive: {result_low.directive}")
    print("Logs:")
    for log in result_low.logs:
        print(f"  - {log}")