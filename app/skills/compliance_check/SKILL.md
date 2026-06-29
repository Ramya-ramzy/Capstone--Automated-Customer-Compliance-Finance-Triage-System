---
name: compliance_check
description: Threshold policy validation for financial triage systems, flagging high-value transactions.
---

# Compliance Check Skill: Financial Threshold Validation

This skill defines the runtime policy validation rules for processing financial payloads in the Customer Compliance & Finance Triage System.

## Compliance Threshold Rule

To enforce administrative oversight and prevent automated processing errors for high-value financial transfers, the system must validate the transaction amount:

> [!IMPORTANT]
> **STRICT THRESHOLD RULE:** Any financial payload amount exceeding **$10,000** must immediately be flagged for manual human triage.

## Validation logic
1. Parse the incoming payload and extract the transaction `amount`.
2. Compare the `amount` against the threshold limit of **10000.00**.
3. If `amount > 10000.00`:
   - Set transaction state status to `FLAGGED_FOR_TRIAGE`.
   - Issue a warning message indicating manual intervention is required.
4. If `amount <= 10000.00`:
   - Set transaction state status to `VERIFIED`.
