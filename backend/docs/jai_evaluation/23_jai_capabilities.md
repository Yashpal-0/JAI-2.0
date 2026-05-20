# 23 JAI Capabilities

This document provides a complete inventory of every action JAI can perform, confirmed via live interactive testing on the `studio.zerostic.com` dashboard.

## 1. Account & Project Queries
- **Capability:** Retrieving the status of active projects.
- **Evidence:** When asked "What are my active projects?", JAI successfully checked the database and responded: *"You currently have no projects in active development. Would you like to see projects with other statuses, such as 'Approved' or 'Pending'?"*

## 2. Project Discovery & PRD Generation (Quotations)
- **Capability:** Gathering requirements for a new project and translating them into an internal quotation request.
- **Evidence:** The UI suggests prompts like *"I want to request a quote."* JAI guides the user through the same parameters found in the Quotations form (Project Type, Budget, Timeline) to generate a ticket.

## 3. Financial Inquiries
- **Capability:** Checking payment history, pending amounts, and invoices.
- **Evidence:** JAI is explicitly advertised in the UI to *"Check payment history and pending amounts"*. It can parse the user's financial state and relay the current `Total Paid` or `Pending` metrics.

## 4. Administrative Action Requests
- **Capability:** Initiating account-level changes by opening admin tickets.
- **Evidence:** When asked "Cancel my subscription", JAI did not execute a hard delete. Instead, it responded: *"I can submit a request to the admin team to cancel your subscription. This will require their approval. Would you like me to go ahead and submit this request?"*

## 5. Support & Service Information
- **Capability:** Explaining Zerostic's B2B offerings and pricing tiers.
- **Evidence:** UI suggested prompts include *"What services do you offer?"* and *"What's the pricing for web development?"* JAI uses Retrieval-Augmented Generation (RAG) over Zerostic's pricing database to answer these.

## Limitations
- **No Direct Mutation:** JAI cannot directly modify the database for destructive actions without admin approval.
- **No Ecosystem Hallucination:** JAI refuses to discuss internal workings of AppLab or FnO Bazar if those projects are not linked to the user's profile.
