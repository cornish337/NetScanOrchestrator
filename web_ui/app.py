import os
import json
from flask import Flask, render_template, abort, url_for, request, redirect, flash # Added request, redirect, flash
import datetime # Added datetime
from multiprocessing import cpu_count # Added cpu_count

# Assuming src is in python path or adjust sys.path if running directly and not as package
# For a packaged app, these imports should work if src is a package
# Adjusting sys.path for local development if 'src' is not installed as a package
import sys
PROJECT_ROOT_FOR_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT_FOR_SRC)
from src.ip_handler import chunk_ips # read_ips_from_file might not be directly used for textarea
from src.parallel_scanner import scan_chunks_parallel
from src.results_handler import consolidate_scan_results, to_json


app = Flask(__name__)
app.secret_key = os.urandom(24) # Needed for flash messages

# Assuming output files are stored in a directory like 'data/cli_outputs'
# relative to the project root.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'data', 'cli_outputs')
PROJECT_FILES_DIR = os.path.join(PROJECT_ROOT, 'data', 'project_files') # New directory for project files

# Ensure PROJECT_FILES_DIR exists
if not os.path.exists(PROJECT_FILES_DIR):
    try:
        os.makedirs(PROJECT_FILES_DIR)
    except OSError as e:
        # Consider logging this error
        print(f"Error creating project files directory {PROJECT_FILES_DIR}: {e}")


# Context processor to make RESULTS_DIR available in templates
@app.context_processor
def inject_results_dir():
    # Return a relative or user-friendly path if needed for display
    # For internal linking, absolute path is fine but not usually shown to user directly in templates.
    # For the example in index.html, we just need a string.
    # Making it relative to project root for display:
    display_results_dir = os.path.relpath(RESULTS_DIR, PROJECT_ROOT)
    return dict(RESULTS_DIR_DISPLAY=display_results_dir)


@app.route('/scan', methods=['POST'])
def run_scan():
    targets_str = request.form.get('targets', '')
    nmap_options = request.form.get('nmap_options', '-T4 -F') # Default options if not provided

    # Define common Nmap scan type flags
    scan_type_flags = [
        "-sS", "-sT", "-sU", "-sA", "-sW", "-sM", # TCP SYN, Connect, UDP, ACK, Window, Maimon
        "-sP", "-sn", # Ping Scan (older Nmap, use -sn), No Port Scan
        "-PR", # ARP Ping
        "-PS", # TCP SYN Ping
        "-PA", # TCP ACK Ping
        "-PU", # UDP Ping
        "-PY"  # SCTP INIT Ping
    ]

    # Check if any scan type flag is already present in nmap_options
    # This is a simplified check; robust parsing of nmap options can be complex.
    # It looks for the flags as standalone words or parts of combined options.
    # For example, it will find "-sS" in "-T4 -sS -O" and also in "-T4sS -O"
    # by checking for the presence of the flag string.
    scan_type_specified = False
    for flag in scan_type_flags:
        if flag in nmap_options:
            scan_type_specified = True
            break

    if not scan_type_specified:
        nmap_options = "-sT " + nmap_options
        app.logger.info(f"No scan type specified. Defaulting to TCP Connect Scan (-sT). New options: '{nmap_options}'")


    processed_targets = [line.strip() for line in targets_str.splitlines() if line.strip()]

    if not processed_targets:
        flash('No targets provided. Please enter at least one IP address or hostname.', 'error')
        return redirect(url_for('index'))

    # Ensure RESULTS_DIR exists
    if not os.path.exists(RESULTS_DIR):
        try:
            os.makedirs(RESULTS_DIR)
        except OSError as e:
            app.logger.error(f"Error creating results directory {RESULTS_DIR}: {e}")
            flash(f"Server error: Could not create results directory. {e}", 'error')
            return redirect(url_for('index'))

    # Chunk IPs
    # Using a default chunk size similar to nmap_parallel_scanner.py, can be made configurable
    ip_chunks = chunk_ips(processed_targets, chunk_size=10)

    num_processes = cpu_count() or 1

    try:
        app.logger.info(f"Starting scan for targets: {processed_targets} with options: '{nmap_options}' using {num_processes} processes.")
        raw_scan_results = scan_chunks_parallel(ip_chunks, nmap_options, num_processes)
        consolidated_data = consolidate_scan_results(raw_scan_results)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"scan_results_{timestamp}.json"
        output_filepath = os.path.join(RESULTS_DIR, new_filename)

        to_json(consolidated_data, output_filepath) # This function prints to console
        app.logger.info(f"Scan results saved to {output_filepath}")
        flash(f"Scan complete! Results saved to {new_filename}", 'success')
        return redirect(url_for('view_results', filename=new_filename))

    except Exception as e:
        app.logger.error(f"Error during scan process: {e}", exc_info=True) # Log stack trace
        flash(f"An error occurred during the scan: {e}", 'error')
        return redirect(url_for('index'))


@app.route('/')
def index():
    # List available JSON result files for viewing
    available_scan_files = []
    if os.path.exists(RESULTS_DIR):
        try:
            available_scan_files = sorted([f for f in os.listdir(RESULTS_DIR) if f.endswith('.json')], reverse=True)
        except OSError as e:
            app.logger.error(f"Error listing files in {RESULTS_DIR}: {e}")
            flash(f"Could not list scan result files: {e}", "error")
            pass # available_scan_files will remain empty

    # List available JSON project configuration files
    available_project_files = []
    if os.path.exists(PROJECT_FILES_DIR):
        try:
            available_project_files = sorted([f for f in os.listdir(PROJECT_FILES_DIR) if f.endswith('.json')], reverse=True)
        except OSError as e:
            app.logger.error(f"Error listing files in {PROJECT_FILES_DIR}: {e}")
            flash(f"Could not list project configuration files: {e}", "error")
            pass # available_project_files will remain empty

    return render_template('index.html', files=available_scan_files, project_files=available_project_files)


from werkzeug.exceptions import BadRequest # Import BadRequest

@app.route('/save_host_config', methods=['POST'])
def save_host_config():
    if not request.is_json: # Check Content-Type header first
        return {"status": "error", "message": "Content-Type must be application/json"}, 415 # Unsupported Media Type

    try:
        config_data = request.get_json()
        # If request.is_json is true, get_json() will parse it.
        # If parsing fails (malformed JSON), it raises a BadRequest (400).
        # If C-T is application/json and body is empty, config_data will be None.
        if config_data is None:
            return {"status": "error", "message": "No JSON data provided in the request body or JSON is null."}, 400

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_config_{timestamp}.json"
        filepath = os.path.join(PROJECT_FILES_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)

        # flash() is not typically useful for API endpoints that return JSON
        # flash(f"Configuration saved successfully as {filename}", 'success')
        app.logger.info(f"Configuration saved successfully as {filename}")
        return {"status": "success", "message": "Configuration saved", "filename": filename}, 200
    except BadRequest as e: # Handles malformed JSON if C-T was application/json
        app.logger.warning(f"Malformed JSON received for save_host_config: {e.description}")
        return {"status": "error", "message": f"Malformed JSON: {e.description}"}, 400
    except Exception as e:
        app.logger.error(f"Error saving host configuration: {e}", exc_info=True)
        # flash(f"Error saving configuration: {e}", 'error')
        return {"status": "error", "message": "An unexpected error occurred while saving configuration."}, 500


@app.route('/load_host_config/<path:filename>', methods=['GET'])
def load_host_config(filename):
    # Security: Normalize the path and ensure it's within PROJECT_FILES_DIR.
    requested_path = os.path.normpath(os.path.join(PROJECT_FILES_DIR, filename))

    if not requested_path.startswith(os.path.abspath(PROJECT_FILES_DIR) + os.sep):
        # Using app.logger for server-side logging of the attempt
        app.logger.warning(f"Potential directory traversal attempt for filename: {filename}")
        return {"status": "error", "message": "Invalid filename or path."}, 400

    if not filename.endswith('.json'):
        return {"status": "error", "message": "Invalid file type. Only JSON files are allowed."}, 400

    filepath = requested_path

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return {"status": "success", "data": config_data}, 200
    except FileNotFoundError:
        app.logger.info(f"Configuration file not found: {filename}")
        return {"status": "error", "message": "Configuration file not found."}, 404
    except json.JSONDecodeError:
        app.logger.error(f"Error decoding JSON from configuration file: {filename}")
        return {"status": "error", "message": "Error decoding JSON from file."}, 500
    except Exception as e:
        app.logger.error(f"Unexpected error loading configuration {filename}: {e}", exc_info=True)
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}, 500


@app.route('/view_results/<path:filename>') # Use <path:filename> to allow slashes if files are in subdirs of RESULTS_DIR
def view_results(filename):
    # Security: Normalize the path and ensure it's within RESULTS_DIR.
    # os.path.normpath helps prevent some traversal, but checking common root is more robust.
    requested_path = os.path.normpath(os.path.join(RESULTS_DIR, filename))

    if not requested_path.startswith(os.path.abspath(RESULTS_DIR) + os.sep):
        abort(400, "Invalid filename or path (directory traversal attempt).")

    # Additional check for filename pattern, e.g., only allow .json
    if not filename.endswith('.json'):
        abort(400, "Only JSON files can be viewed currently.")

    filepath = requested_path # Use the normalized and validated path

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # The 'protocols' key might not exist if a host is down or no ports scanned.
        # The template expects 'host_details.protocols'.
        # Let's ensure it's there, or an empty dict, for hosts that are up.
        # This kind of data massaging could also be done in consolidate_scan_results.
        for _ip, host_data in data.get('hosts', {}).items():
            if 'protocols' not in host_data:
                host_data['protocols'] = {} # Ensure template doesn't break
            if 'status' not in host_data: # Ensure status is present
                host_data['status'] = {'state': 'unknown', 'reason': 'N/A'}


        return render_template('results_display.html', data=data, filename=filename)
    except FileNotFoundError:
        abort(404, "Result file not found.")
    except json.JSONDecodeError:
        abort(500, "Error decoding JSON from the result file.")
    except Exception as e:
        # Log the actual exception here for debugging
        app.logger.error(f"Unexpected error processing {filename}: {e}")
        abort(500, f"An unexpected error occurred. Please check server logs.")

if __name__ == '__main__':
    # Ensure RESULTS_DIR exists for the demo or provide instructions.
    if not os.path.exists(RESULTS_DIR):
        try:
            os.makedirs(RESULTS_DIR)
            print(f"Created results directory for web UI: {RESULTS_DIR}")
            print(f"Please place some .json scan output files (e.g., from CLI output) in '{RESULTS_DIR}' to test the web UI.")
        except OSError as e:
            print(f"Error creating results directory {RESULTS_DIR}: {e}")
            print("Please create it manually and place JSON scan results there.")

    print(f"Flask app running. Access at http://127.0.0.1:5000")
    print(f"Serving results from: {os.path.abspath(RESULTS_DIR)}")
    # Note: app.run() is only for development. For production, use a WSGI server like Gunicorn.

    # Ensure PROJECT_FILES_DIR also exists at startup (though created above, good for standalone run)
    if not os.path.exists(PROJECT_FILES_DIR):
        try:
            os.makedirs(PROJECT_FILES_DIR)
            print(f"Created project files directory: {PROJECT_FILES_DIR}")
        except OSError as e:
            print(f"Error creating project files directory {PROJECT_FILES_DIR}: {e}")

    app.run(debug=True, host='0.0.0.0', port=5000) # Listen on all interfaces for easier access if in a VM/container. Explicit port.
