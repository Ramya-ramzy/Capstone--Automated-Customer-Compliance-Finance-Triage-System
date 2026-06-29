from app.agent import run_triage_pipeline
import json

def print_divider(title):
    print(f"\n{'='*20} {title} {'='*20}")

# --- CASE 1: Standard compliant invoice ---
print_divider("TEST CASE 1: Standard Invoice Processing")
safe_invoice = {
    "id": "INV-2026-001",
    "vendor": "Global Data Cloud Corp",
    "amount": 4500.00
}
result_1 = run_triage_pipeline(safe_invoice)
print(f"System Action:  {result_1['action']}")
print(f"System Message: {result_1['message']}")
print(f"Final Internal State: {result_1['payload']['compliance_status']}")


# --- CASE 2: High-Value Anomaly ---
print_divider("TEST CASE 2: High-Value Triage Routing")
anomaly_invoice = {
    "id": "INV-2026-999",
    "vendor": "Enterprise Hardware Hub",
    "amount": 27500.00
}
result_2 = run_triage_pipeline(anomaly_invoice)
print(f"System Action:  {result_2['action']}")
print(f"System Message: {result_2['message']}")
# Extracting the correct state parameter directly from the payload object
print(f"Final Internal State: {result_2['payload']['compliance_status']}")
print('='*50)