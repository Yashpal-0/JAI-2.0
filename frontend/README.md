# 🎨 Zerostic JAI 2.0 — Frontend Web Client

The frontend client of JAI 2.0 is a highly responsive, high-performance single page application built on React 18, TypeScript, and Vite. It is designed to deliver a premium user experience through bespoke, smooth CSS transitions, modern typography, glassmorphic layout elements, and dynamic glowing background orbs that bring the interactive AI session to life.

---

## ✨ Features

- 🌌 **Premium Aurora UI Theme**: Visual identity with glowing, animated background orbs and a beautiful glassmorphic layout using modern CSS properties.
- 📱 **Responsive Sidebar & Chat Panel**: Desktop and mobile friendly layout, featuring a slide-out drawer list containing active sessions, custom session creations, and thread removals.
- 🏢 **Multi-Tenant Integration**: Live switching between tenant profiles (e.g. `zerostic.com`), aligning headers and configurations accordingly.
- 🔄 **Real-Time Token-Level Streaming**: Fully async SSE streams using native Server-Sent Events, displaying JAI's responses instantly as they are calculated.
- 🛡️ **Session Persistence**: Automated syncs that link active user IDs and thread tokens with the FastAPI/SQLite databases.
- 🧪 **Vitest Test Suite**: Pre-configured unit and component tests with `jsdom` and `@testing-library/react`.

---

## 🛠️ Tech Stack & Requirements

- **Framework**: [React 18 (TypeScript)](https://react.dev/)
- **Build Tool**: [Vite 5](https://vitejs.dev/)
- **Styles**: Raw Vanilla CSS (Tailwind-free for maximum customization, absolute control, and top-tier layout flexibility)
- **Tests**: [Vitest](https://vitest.dev/) & [JSDom](https://github.com/jsdom/jsdom)
- **Node.js Requirement**: v18.0.0 or higher
- **Package Manager**: `npm` (v9+)

---

## 🚀 Setup & Development

### 1. Installation
Navigate into the `frontend` subdirectory and install local dependencies:
```bash
cd frontend
npm install
```

### 2. Running the Dev Server
Launch Vite's hot-reloading dev server:
```bash
npm run dev
```
By default, the client starts up on **`http://localhost:5173`**.

---

## 🔗 How API Proxying Works

To bypass Cross-Origin Resource Sharing (CORS) limits during local development without cluttering your React code with absolute URLs, a local server proxy is declared inside `vite.config.ts`. 

Whenever your React application triggers a fetch call to a relative path:
- `/chat`
- `/threads`
- `/health`

Vite automatically catches the request and routes it to `http://localhost:8000`.

> [!TIP]
> Ensure your backend is running on `localhost:8000` (FastAPI's default port) so that the proxy resolves successfully.

---

## 📂 Source Code Structure

Inside `frontend/src/`:
- **`App.tsx`**: Main component that connects the layout structure, controls thread switching, hooks into tenant profiles, and calls background APIs.
- **`components/`**: 
  - `Sidebar.tsx`: Session drawer listing active chat instances, timestamps, and thread removals.
  - `ChatWindow.tsx`: Interactive chat area formatting user messages and streaming assistant bubbles (with custom markdown parsing).
  - `TenantSelector.tsx`: Theme-conforming dropdown selector for swapping active context domains.
- **`hooks/`**:
  - `useChat.ts`: Custom hook managing active server SSE streaming, parsing individual chunks, accumulating states, handling connection errors, and caching messages.
- **`index.css`**: The core design system. Defines responsive layouts, CSS variables, glassmorphic filters, keyframe animations, and custom scrollbar overlays.
- **`types.ts`**: TypeScript type blueprints for Threads, Tenants, Messages, and App settings.

---

## 🧪 Testing

Running the frontend test suite is simple. The workspace uses `Vitest` for lightning-fast unit verification.

Run all tests:
```bash
npm run test
```

Vite will run the unit testing pipeline (`App.test.tsx`, component tests, etc.) in a virtual JSDOM environment, providing immediate status checks on inputs, state transitions, and component mounts.

---

## 📦 Production Bundling

To generate a highly optimized static bundle for hosting on production hosts (e.g. Firebase Hosting, Netlify, or Vercel):
```bash
npm run build
```
This command compiles TypeScript files via `tsc` and runs Vite's roll-up optimizer to write optimized, compressed HTML/JS/CSS assets into a `dist/` folder.
