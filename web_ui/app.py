import os
import json
from flask import Flask, render_template, abort, url_for

app = Flask(__name__)

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
    app.run(debug=True, host='0.0.0.0') # Listen on all interfaces for easier access if in a VM/container
```
