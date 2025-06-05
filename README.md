# Parallel Nmap Scanner with Web UI

This project provides a Python-based Nmap scanner that can run scans in parallel for efficiency, along with a web interface for initiating scans and viewing results.

## Features

*   Parallel scanning of multiple targets.
*   Web UI for easy interaction.
*   Displays Nmap scan results.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```
2.  Create a virtual environment and activate it:
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    ```
3.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Start the Flask web server:
    ```bash
    python web_ui/app.py
    ```
2.  Open your web browser and navigate to `http://127.0.0.1:5000`.
3.  Enter the IP addresses or hostnames to scan and click "Scan".

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -am 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Create a new Pull Request.
