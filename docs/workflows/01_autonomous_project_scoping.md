# 01 Autonomous Project Scoping & PRD Generator

## Context
Extracted from `studio.zerostic.com/quotations` and JAI interactions, we know the intake currently uses:
- Project Types: Web Application, Mobile Application, API/Backend, UI/UX Design, E-commerce, Custom Software
- Budgets: Range-based (Under ₹50,000 to ₹25,000,000+)
- Timelines: ASAP to Flexible
- JAI currently acts as a conversational requirements gatherer.

## Predictive Marketplace Enhancement
In a decentralized marketplace pivot, the PRD generator acts as the **bridge** between the Client Dashboard and the PM Dashboard. 

### Data Requirements & Variables
- `client_intent_raw`: Raw conversational logs from JAI.
- `tech_stack_inferred`: Extracted from JAI logic rules.
- `pm_vetting_checklist`: A boolean matrix required for PM acceptance.

### Pipeline Logic Flow
1. **Intake Trigger:** Client clicks "Chat with JAI" -> selects "I want to request a quote".
2. **Conversational Extraction:** JAI uses RAG to pull pricing constraints.
3. **PRD Structuring:** LLM pipeline compiles user intent into a structured JSON `PRD_Draft`.
4. **Marketplace Routing:** `PRD_Draft` is pushed to a Kafka topic `marketplace_opportunities`.
5. **PM Acceptance:** Independent Product Managers bid on or accept the PRD in their decoupled dashboard.
