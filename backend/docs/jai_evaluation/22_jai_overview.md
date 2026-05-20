# 22 JAI Overview

## What is JAI?
JAI is the native, AI-powered conversational assistant integrated directly into **Zerostic Studio**, the authenticated B2B client portal for Zerostic.

## Persona and Positioning
JAI is designed to act as a **Client Success & Account Manager**. It does not present itself as an open-ended generative tool (like a standard ChatGPT interface); instead, it operates within strict constraints tailored to the user's authenticated context. 

## Primary Interface
- **Access Point:** Located at `https://studio.zerostic.com/jai`. It is accessible via the "Chat with JAI" CTA button present on the bottom left of the global navigation sidebar.
- **UI Structure:** It utilizes a traditional chat interface with an input box at the bottom (`[placeholder="Type your message..."]`) and maintains a threaded history of past conversations ("History X", "New Chat").

## Core Operational Directives
Based on extensive interactive probing, JAI operates under the following directives:
1. **Context Boundary Enforcement:** It refuses to discuss or invent details about projects that do not belong to the currently authenticated user.
2. **Action Delegation:** For destructive actions (like "Cancel my subscription") or creation actions (like "Request a quote"), it acts as an intermediary. It parses the intent and offers to "submit a request to the admin team."
3. **Information Retrieval:** It can query the underlying database for user-specific metrics (e.g., active project count, pending payments).

## Disclaimer
The UI prominently features the disclaimer: *"JAI can make mistakes. Verify important information."*
