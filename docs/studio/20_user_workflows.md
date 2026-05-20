# 20 User Workflows (End-to-End Client Journey)

## Overview
The Zerostic Studio acts as a traditional B2B software agency portal. Based on authenticated DOM extraction, the end-to-end client journey follows a strictly gated progression: Verification -> Scoping -> Contracting -> Execution -> Billing.

## 1. Onboarding & Verification Workflow
**Trigger:** Client lands on `/dashboard` or `/settings`.
- **Goal:** Verify the identity of the lead client before full service execution.
- **UI Elements:** "Government ID Required" alert on the dashboard.
- **Action:** User clicks `Upload ID` -> Submits government-issued proof.
- **State Change:** Account transitions from `Unverified` to `Verified`, unlocking contract execution.

## 2. Project Scoping & Quotations Workflow
**Trigger:** Client navigates to `/quotations` or clicks `Chat with JAI`.
- **Goal:** Define the technical and financial bounds of a new project.
- **Path A (Form):** Click `Request Quotation` -> Fill Project Type, Description, Budget Range, Timeline -> Submit.
- **Path B (JAI):** Converse with JAI -> JAI extracts requirements -> Synthesizes into an internal ticket for the Admin.

## 3. Contracting Workflow
**Trigger:** Admin processes quotation and sends a contract -> Client navigates to `/contracts`.
- **Goal:** Legally bind the scoped project.
- **UI Elements:** List of pending/signed contracts.
- **Action:** Review contract terms -> Sign electronically.

## 4. Project Execution Tracking
**Trigger:** Contract signed -> Project moves to `/projects`.
- **Goal:** Provide transparency into development progress.
- **UI Elements:** Project cards, Search bar, Status filters (e.g., Active, Completed).
- **Client Action:** Passive viewing of status updates provided by the admin.

## 5. Billing & Payments Workflow
**Trigger:** Admin requests payment -> Client navigates to `/payments`.
- **Goal:** Process manual B2B transactions.
- **Mechanism:** Zerostic relies on manual bank transfers (NEFT, RTGS, IMPS, UPI).
- **Action:** User makes off-platform transfer -> Clicks `Upload Payment Proof` -> Submits transaction ID/Receipt.
- **Validation:** Admin verifies receipt -> Updates `Total Paid` and `Pending` metrics.

## 6. Invoicing
**Trigger:** Payment processed -> Admin issues invoice -> Client navigates to `/invoices`.
- **Goal:** Tax compliance and record keeping.
- **Action:** Search by invoice number -> Download PDF.

## 7. Direct Communication & Scheduling
- **Asynchronous (`/messages`):** Threaded chat system (e.g., "General Inquiry" with "Admin").
- **Synchronous (`/scheduler`):** Book Google Calendar/Meet video calls for:
  - Project Consultation (60 min)
  - Technical Discussion (45 min)
  - Demo/Presentation (30 min)
  - Support Session (30 min)
