# 21 UI Component Map

## Common Layout Elements
- **Sidebar Navigation:**
  - Persistent left-hand column containing links with SVG icons for Dashboard, Projects, Contracts, Payments, Invoices, Messages, Notifications, Quotations, Scheduler.
  - Persistent "Chat with JAI" CTA button located at the bottom of the navigation block.
- **Top Banner:**
  - Theme toggle button (Dark/Light mode).
  - Notification bell (shows unread badge count).
  - User Avatar dropdown (Name, Email, Sign Out).

## Core Reusable Components

### Metric Cards (`<MetricCard />`)
- **Location:** Primarily `/dashboard` and `/payments`.
- **States:** Title (e.g., "Active Projects", "Total Paid"), large integer or currency value, and an accompanying icon.
- **Data Hook:** Fetches summary aggregations via `_rsc` server-component payloads.

### Data Tables / List Views (`<DataList />`)
- **Location:** `/projects`, `/contracts`, `/invoices`.
- **States:** 
  - Populated: Rows of data.
  - Empty State: "No [items] found" with an illustrative SVG and a descriptive paragraph (e.g., "You don't have any projects yet.").
- **Interactions:** Top-right search bar (`input[type="text"]`) and a Status Filter combobox ("All Statuses").

### Forms & Modals (`<QuotationModal />`, `<PaymentProofModal />`)
- **Location:** Triggered by buttons on `/quotations` and `/payments`.
- **Components:**
  - `Combobox` (Dropdowns for project type, budget).
  - `File Uploader` (Drag-and-drop or click to upload ID/receipts).
  - `Textarea` (With character count validation like "0/50 characters minimum").
  - `Submit Button` (Disabled until validation passes).

### Chat Interface (`<JaiChat />`, `<MessageThread />`)
- **Location:** `/jai`, `/messages`.
- **Components:**
  - Message history scroll view.
  - Input container fixed at bottom (`input[text]` + `Submit Button`).
  - Disclaimer text ("JAI can make mistakes. Verify important information.").
