# Nmap Parallel Scanner

This project contains a real-time "Nmap Parallel Scanner" control panel.

## Structure

- `backend/`: FastAPI + Uvicorn backend
- `frontend/`: SvelteKit + Tailwind CSS frontend

## Running the application

### Backend

1.  Navigate to the backend directory:
    ```sh
    cd backend
    ```

2.  Install dependencies:
    ```sh
    pip install fastapi uvicorn pydantic "python-multipart"
    ```
    *(Note: `python-multipart` is needed for `UploadFile`)*

3.  Run the server:
    ```sh
    uvicorn main:app --reload
    ```
    The backend will be running at `http://localhost:8000`.

    A one-off scan can be triggered via:

    ```sh
    curl -X POST http://localhost:8000/nmap/run \
      -H 'Content-Type: application/json' \
      -d '{"target": "scanme.nmap.org"}'
    ```
    The response includes the executed command and parsed scan results.

### Frontend

1.  Navigate to the frontend directory:
    ```sh
    cd frontend
    ```

2.  Install dependencies:
    ```sh
    npm install
    ```

3.  Run the development server:
    ```sh
    npm run dev
    ```
    The frontend will be running at `http://localhost:5173`.

Open [http://localhost:5173](http://localhost:5173) in your browser to see the application.
