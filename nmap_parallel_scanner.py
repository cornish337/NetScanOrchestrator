import argparse
import os
import sys
from multiprocessing import cpu_count

# Adjust path to import from src, assuming the script is in the root
# and src is a subdirectory.
# This allows the script to be run from any directory if it's directly executed.
# However, for packaging, a different approach (e.g. setup.py) would be better.
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_dir, 'src'))
# If 'src' is not found relative to script, try relative to current working directory
# This helps if the script is called from the project root like "python nmap_parallel_scanner.py"
if not os.path.exists(os.path.join(script_dir, 'src', 'ip_handler.py')):
    sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), '.')))


from ip_handler import read_ips_from_file, chunk_ips
from parallel_scanner import scan_chunks_parallel
from results_handler import (
    consolidate_scan_results,
    to_json,
    to_csv,
    to_txt,
    to_markdown,
    to_xml
)

def main():
    parser = argparse.ArgumentParser(
        description="Parallel Nmap Scanner: Conducts Nmap scans in parallel on a list of targets.",
        formatter_class=argparse.RawTextHelpFormatter # Allows for better formatting of help messages
    )
    parser.add_argument(
        "-i", "--input-file",
        required=True,
        help="Path to the file containing IP addresses or network ranges (one per line)."
    )
    parser.add_argument(
        "-o", "--output-prefix",
        required=True,
        help="Prefix for output file names (e.g., 'scan_results/security_audit_q1'). Directory will be created if it doesn't exist."
    )
    parser.add_argument(
        "-f", "--formats",
        default="json,csv,txt,md,xml",
        help="Comma-separated list of output formats (json, csv, txt, md, xml).\nDefault: all formats."
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10,
        help="Number of IPs/ranges per chunk for parallel scanning.\nDefault: 10."
    )
    parser.add_argument(
        "--num-processes",
        type=int,
        default=None,
        help="Number of parallel Nmap processes to run.\nDefault: number of CPU cores available to the system."
    )
    parser.add_argument(
        "--nmap-options",
        default="-T4 -F",
        help="Nmap command-line options string.\nDefault: '-T4 -F' (aggressive timing, fast scan - 100 common ports)."
    )

    args = parser.parse_args()

    if args.num_processes is None:
        args.num_processes = cpu_count()
        if args.num_processes is None: # cpu_count() can return None
            print("Warning: Could not determine number of CPU cores. Defaulting to 1 process.")
            args.num_processes = 1
    elif args.num_processes <= 0:
        print("Warning: --num-processes must be greater than 0. Defaulting to 1 process.")
        args.num_processes = 1

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output_prefix)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error creating output directory {output_dir}: {e}. Please check permissions or path.")
            return

    print(f"Starting Nmap Parallel Scanner with the following settings:")
    print(f"  Input file:      {args.input_file}")
    print(f"  Output prefix:   {args.output_prefix}")
    print(f"  Output formats:  {args.formats}")
    print(f"  Chunk size:      {args.chunk_size}")
    print(f"  Num processes:   {args.num_processes}")
    print(f"  Nmap options:    {args.nmap_options}")
    print("-" * 40)

    # 1. Read IPs
    print(f"Step 1/5: Reading IPs from '{args.input_file}'...")
    ips_to_scan = read_ips_from_file(args.input_file)
    if not ips_to_scan:
        # read_ips_from_file now prints its own error for FileNotFoundError
        # print(f"No IPs found in '{args.input_file}' or file could not be read. Exiting.")
        return
    print(f"          Found {len(ips_to_scan)} IP(s)/range(s).")

    # 2. Chunk IPs
    print(f"Step 2/5: Chunking IPs into groups of {args.chunk_size}...")
    # Pass custom_ranges=None explicitly, though it's the default
    ip_chunks = chunk_ips(ips_to_scan, chunk_size=args.chunk_size, custom_ranges=None)
    if not ip_chunks:
        print("          No IP chunks to scan (perhaps the input list was empty after processing). Exiting.")
        return
    print(f"          Created {len(ip_chunks)} chunk(s).")

    # 3. Run scans in parallel
    print(f"Step 3/5: Starting Nmap scans for {len(ip_chunks)} chunk(s) using {args.num_processes} parallel process(es)...")
    print(f"          Nmap options for scan: '{args.nmap_options}'")
    # This step can take a while.
    raw_scan_results = scan_chunks_parallel(ip_chunks, args.nmap_options, args.num_processes)

    if not raw_scan_results:
        print("          Parallel scanning returned no results at all. This could be due to an issue in the parallel processing module or if all chunks immediately failed before returning data. Exiting.")
        return

    # Check if all results are errors (e.g. nmap not found in any process)
    all_failed = True
    for r in raw_scan_results:
        if isinstance(r, dict) and not r.get("error"):
            all_failed = False
            break
    if all_failed:
        print("          All scan chunks resulted in errors. Check error details in logs or JSON output if produced. Common issues: Nmap not installed/not in PATH for subprocesses, invalid Nmap options, or permission issues.")
        # We'll still proceed to consolidate and output these errors.
    else:
        print("          Parallel scanning phase complete.")

    # 4. Consolidate results
    print("Step 4/5: Consolidating scan results...")
    consolidated_data = consolidate_scan_results(raw_scan_results)

    if not consolidated_data.get("hosts") and consolidated_data.get("errors"):
        print("          Consolidation complete: No responsive hosts found, but errors were reported during scans.")
    elif not consolidated_data.get("hosts"):
        print("          Consolidation complete: No responsive hosts found, or no data retrieved from scans that identified live hosts/ports.")
    else:
        print(f"          Consolidation complete: Found data for {len(consolidated_data.get('hosts', {}))} unique host(s).")

    # 5. Save results in specified formats
    print(f"Step 5/5: Saving results to files with prefix '{args.output_prefix}'...")
    output_formats = [fmt.strip().lower() for fmt in args.formats.split(',') if fmt.strip()]

    output_handlers = {
        "json": to_json,
        "csv": to_csv,
        "txt": to_txt,
        "md": to_markdown,
        "xml": to_xml
    }

    any_output_successful = False
    for fmt in output_formats:
        if fmt in output_handlers:
            # Ensure output_prefix is used as a prefix, not a directory itself if it looks like one
            base_output_name = os.path.basename(args.output_prefix)
            output_filename = os.path.join(output_dir, f"{base_output_name}.{fmt}")

            print(f"  Saving to {output_filename} (format: {fmt.upper()})...")
            try:
                output_handlers[fmt](consolidated_data, output_filename)
                any_output_successful = True
            except Exception as e:
                print(f"    Error saving to {fmt} format at {output_filename}: {e}")
        else:
            print(f"  Warning: Unknown or unsupported format '{fmt}' specified. Skipping.")

    print("-" * 40)
    if any_output_successful:
        print("Nmap Parallel Scanner finished successfully. Output files are located with the prefix:")
        print(f"  {os.path.abspath(args.output_prefix)}.<format>")
    else:
        print("Nmap Parallel Scanner finished, but no output files were successfully generated.")
        print("Please check logs for errors, especially if formats were specified but failed.")


if __name__ == "__main__":
    # This allows the script to be run directly.
    # For a packaged application, entry points in setup.py would be used.
    main()
```
