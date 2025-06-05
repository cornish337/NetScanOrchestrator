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
    available_files = []
    if os.path.exists(RESULTS_DIR):
        try:
            available_files = sorted([f for f in os.listdir(RESULTS_DIR) if f.endswith('.json')], reverse=True)
        except OSError as e:
            print(f"Error listing files in {RESULTS_DIR}: {e}")
            # Optionally, pass an error message to the template
            pass # available_files will remain empty

    return render_template('index.html', files=available_files)

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
    app.run(debug=True, host='0.0.0.0', port=5000) # Listen on all interfaces for easier access if in a VM/container. Explicit port.
```
