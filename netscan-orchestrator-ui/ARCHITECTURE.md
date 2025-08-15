# NetScanOrchestrator Frontend Architecture

This document outlines the architecture for the NetScanOrchestrator frontend application. It details the project structure, component hierarchy, data flow, and state management strategies.

## 1. Guiding Principles

- **Component-Based:** The UI is built as a collection of reusable, loosely-coupled components.
- **State Management:** Global state is minimized. Server state is managed by `React Query`, while real-time updates are handled via `Socket.IO`. Local component state is used for UI-specific concerns.
- **TypeScript First:** The entire codebase uses TypeScript for type safety and improved developer experience.
- **Styling:** `TailwindCSS` is used for utility-first styling to ensure consistency and rapid development.
- **Animations:** `Framer Motion` is used for all animations to create a polished and interactive user experience.

## 2. Tech Stack

- **Framework:** React 18+
- **Language:** TypeScript
- **Build Tool:** Vite
- **Styling:** TailwindCSS
- **Animations:** Framer Motion
- **Data Fetching:** React Query (`@tanstack/react-query`)
- **Real-time Updates:** Socket.IO Client
- **Charting/Visualization:** Recharts
- **Icons:** Lucide React

## 3. Directory Structure

The `src` directory is organized as follows:

```
src
├── assets/         # Static assets like images, fonts
├── components/     # Reusable UI components (e.g., Button, Modal, Table)
│   ├── common/     # Generic, app-wide components
│   └── features/   # Components specific to a feature (e.g., dashboard, wizard)
├── hooks/          # Custom React hooks (e.g., useScanUpdates, useDebounce)
├── lib/            # Utility functions and helpers (e.g., date formatting, CIDR expansion)
├── pages/          # Top-level page components corresponding to routes
├── services/       # API interaction logic (e.g., API client setup)
├── types/          # TypeScript type definitions and interfaces
└── App.tsx         # Main application component with routing
└── main.tsx        # Application entry point
└── index.css       # Global styles and Tailwind directives
```

## 4. Component Hierarchy (High-Level)

The application is composed of several main pages and a hierarchy of components within them.

```
<App>
  <QueryClientProvider>
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<TargetInputPage />} />
          <Route path="/dashboard" element={<ScanDashboardPage />} />
          <Route path="/difficult-targets" element={<DifficultTargetsPage />} />
        </Routes>
      </MainLayout>
    </Router>
  </QueryClientProvider>
</App>
```

- **`TargetInputPage`**: Contains the `TargetInputWizard` component.
- **`ScanDashboardPage`**: The main monitoring view.
  - `TopControlBar`: Global scan actions.
  - `ScanChunkTable`: Displays real-time progress of scan chunks.
  - `ScanHeatmap`: Visualizes the entire scan range.
  - `EventLog`: Shows a timeline of scan events.
- **`DifficultTargetsPage`**:
  - `DifficultTargetsTable`: A filterable table for failed/slow targets.
  - `RetryModal`: A modal to configure and trigger retries.

## 5. Data Flow and State Management

### Server State (React Query)

- **Purpose:** Used for fetching, caching, and managing data from the REST API.
- **Usage:**
  - `useQuery` is used for fetching data like initial scan states, scan history, and target details.
  - `useMutation` is used for sending data to the server, such as starting/stopping scans or retrying targets.
- **Example:** Fetching the list of difficult targets.
  ```typescript
  // inside a component
  const { data, isLoading } = useQuery({
    queryKey: ['difficult-targets'],
    queryFn: () => api.getDifficultTargets(),
  });
  ```

### Real-time State (Socket.IO)

- **Purpose:** To receive live updates from the backend about scan progress.
- **Usage:**
  - A custom hook, `useScanUpdates`, will encapsulate the Socket.IO connection logic.
  - This hook will connect to the WebSocket server and listen for events (e.g., `chunk_update`, `scan_completed`).
  - When an event is received, it will update the React Query cache using `queryClient.setQueryData`. This ensures that all components subscribed to that data will re-render with the new information, maintaining a single source of truth.
- **Example Flow:**
  1. WebSocket event `chunk_update` is received with new chunk data.
  2. The `useScanUpdates` hook calls `queryClient.setQueryData(['scan-chunks', chunkId], newChunkData)`.
  3. The `ScanChunkTable` and `ScanHeatmap`, which use `useQuery` to get chunk data, automatically re-render with the updated information.

### Local UI State

- **Purpose:** For state that is specific to a single component and does not need to be shared.
- **Usage:** `useState` and `useReducer` hooks.
- **Examples:**
  - Form input state within the `TargetInputWizard`.
  - The open/closed state of a modal.
  - Toggled filters on a table.
