# Automated Customer Compliance & Finance Triage System

An enterprise-grade, graph-based multi-agent system built using Python and the **ADK 2.0 framework**. This project automates straight-through processing for standard compliance and invoice payloads while enforcing strict, localized security boundaries and **Human-in-the-Loop** verification gates for transactional anomalies.

---

## 🚀 System Design & Business Logic

The triage pipeline utilizes three sequentially connected node agents processing an immutable `GraphState`:
1. **Extraction Node:** Standardizes payload keys (accepting `invoice_id`/`id`, `vendor_name`/`vendor`) and parses input data.
2. **Policy Validation Node:** Checks validation logic (Strict threshold of **$10,000** for automated clearing).
3. **Triage Routing Node:** Decides the downstream routing action based on policy evaluation, resolving to `COMMIT_TO_LEDGER` or `SUSPEND_AUTOMATION`.

For a full breakdown of the architecture, refer to [DNA.md](file:///o:/New%20folder/AI_Agent_5days/Project/DNA.md).

---

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.11+

### Installation
1. Clone or navigate to the directory.
2. Create and activate a local virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```

---

## 🔍 Running the Verification Script

To execute the triage pipeline verify command and view pipeline actions for compliant versus high-value invoices:

```bash
python run.py
```

### Expected Output
```text
==================== TEST CASE 1: Standard Invoice Processing ====================
System Action:  COMMIT_TO_LEDGER
System Message: SUCCESS: Invoice INV-2026-001 approved automatically.
Final Internal State: APPROVED

==================== TEST CASE 2: High-Value Triage Routing ====================
System Action:  SUSPEND_AUTOMATION
System Message: ALERT: Manual review needed for Invoice INV-2026-999. Reason: Transaction exceeds standard threshold limit of $10000.0.
Final Internal State: FLAGGED_FOR_TRIAGE
==================================================
```

---

## 🧪 Testing

To run the local unit tests and verify code compliance:

```bash
pytest
```
This tests standard ledger approval, anomalous threshold suspension, exact boundary rules, and extraction error handling (missing fields or invalid amount formatting).
