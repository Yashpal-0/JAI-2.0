# 19 Studio Features & Interactions

## 1. Identity Verification
- **Description:** Mandates government-issued ID upload to unlock full portal capabilities.
- **Inputs:** File upload widget (`input[type="file"]`).
- **Outputs:** Verification status flag (Pending, Verified, Rejected).

## 2. JAI Assistant
- **Description:** An LLM-powered assistant bounded to the client's specific context.
- **Inputs:** Textbox (`input[type="text"]` or `textarea`).
- **Capabilities:**
  - View project status & details
  - Get service & pricing information
  - Submit quotation requests
- **Limits:** Hardcoded refusal to share system prompts or hallucinate architectures for projects not owned by the client.

## 3. Project Scoping Form (Quotations)
- **Description:** Structured intake for new work.
- **Inputs:**
  - `Project Type`: Dropdown (Web, Mobile, API, UI/UX, E-commerce, Custom Software).
  - `Description`: Textarea (50 character minimum).
  - `Estimated Budget`: Dropdown (Under ₹50k to ₹25L+).
  - `Expected Timeline`: Dropdown (ASAP, 1-2 weeks, up to 3-6 months, Flexible).
- **Outputs:** Generation of an internal Quotation Ticket.

## 4. Manual Payment Verification
- **Description:** Off-platform payment reconciliation.
- **Mechanism:** Displays NEFT, RTGS, IMPS, or UPI details to the client.
- **Inputs:** "Upload Payment Proof" button opening a file upload modal.
- **Outputs:** Status change on the `/payments` tracking board.

## 5. Scheduler
- **Description:** Book video calls with the team (Mon-Fri, 9:00 AM - 6:00 PM IST).
- **Options:**
  - Project Consultation (60 min)
  - Technical Discussion (45 min)
  - Demo/Presentation (30 min)
  - Support Session (30 min)
- **Outputs:** Generates a Google Calendar invite with a meeting link.
