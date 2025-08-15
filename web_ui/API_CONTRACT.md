# NetScanOrchestrator API Contract

This document outlines the API endpoints that the frontend application expects the Python/Flask backend to provide.

## Authentication

(To be defined - for now, no authentication is required for local development.)

---

## Configuration Management

These endpoints are used for saving and loading scan configurations (batches of hosts). The frontend will be built to use these existing endpoints.

### 1. Save Host Configuration

*   **Endpoint:** `POST /save_host_config`
*   **Request Body:**
    ```json
    {
      "unassigned_hosts": ["host1.example.com", "192.168.1.10"],
      "batches": {
        "Batch 1 - Critical Servers": ["10.0.0.1", "10.0.0.2"],
        "Batch 2 - Workstations": ["192.168.2.100"]
      }
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
      "status": "success",
      "message": "Configuration saved",
      "filename": "project_config_20250814_193339.json"
    }
    ```
*   **Error Response (400/500):**
    ```json
    {
      "status": "error",
      "message": "Error description."
    }
    ```

### 2. Load Host Configuration

*   **Endpoint:** `GET /load_host_config/<filename>`
*   **Success Response (200 OK):**
    ```json
    {
        "status": "success",
        "data": {
            "unassigned_hosts": ["host1.example.com", "192.168.1.10"],
            "batches": {
                "Batch 1 - Critical Servers": ["10.0.0.1", "10.0.0.2"]
            }
        }
    }
    ```
*   **Error Response (404/500):**
    ```json
    {
        "status": "error",
        "message": "Error description."
    }
    ```

---

## Scan Management (New Asynchronous Flow)

This section describes the **new, required** asynchronous API for starting, monitoring, and managing scans. This is a departure from the current synchronous `POST /scan` endpoint.

### 1. Start a New Scan

*   **Endpoint:** `POST /api/scans`
*   **Description:** Submits a new scan job. The backend should start the scan in a background process and immediately return a scan ID.
*   **Request Body:**
    ```json
    {
      "targets": ["scanme.nmap.org", "192.168.1.0/24"],
      "nmap_options": "-T4 -F"
    }
    ```
*   **Success Response (202 Accepted):**
    ```json
    {
      "scan_id": "a-unique-scan-identifier-uuid-or-timestamp"
    }
    ```

### 2. Get Scan Status and Results

*   **Endpoint:** `GET /api/scans/<scan_id>`
*   **Description:** Retrieves the current status and partial results of a scan. This will be used for polling updates (in addition to WebSockets).
*   **Success Response (200 OK):**
    ```json
    {
      "scan_id": "a-unique-scan-identifier",
      "status": "RUNNING", // PENDING | RUNNING | COMPLETED | FAILED
      "progress": {
        "total_chunks": 100,
        "completed_chunks": 50,
        "failed_chunks": 2
      },
      "results": {
        // Consolidated results will be streamed here or loaded when complete
        "hosts": {
          "192.168.1.1": { "status": "up", "ports": [...] },
          "192.168.1.2": { "status": "down", "reason": "no-response" }
        }
      }
    }
    ```

### 3. Real-time Scan Updates (WebSocket)

*   **Endpoint:** `ws://<host>/ws/scans/<scan_id>`
*   **Description:** A WebSocket connection for receiving real-time updates about a scan, reducing the need for constant polling.
*   **Message Format:** The server will push JSON messages to the client.

    *   **Chunk Update Message:**
        ```json
        {
          "type": "CHUNK_UPDATE",
          "payload": {
            "chunk_id": "chunk-5-of-100",
            "status": "COMPLETED", // PENDING | RUNNING | COMPLETED | FAILED | STUCK
            "result": { /* ... nmap result for this chunk ... */ }
          }
        }
        ```
    *   **Scan Completion Message:**
        ```json
        {
          "type": "SCAN_COMPLETE",
          "payload": {
            "scan_id": "a-unique-scan-identifier",
            "status": "COMPLETED",
            "final_results_url": "/api/scans/<scan_id>"
          }
        }
        ```
---
