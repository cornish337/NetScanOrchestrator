import argparse
import os
import sys
from multiprocessing import cpu_count

# Adjust path to import from src, assuming the script is in the root
# and src is a subdirectory.
# This allows the script to be run from any directory if it's directly executed.
# However, for packaging, a different approach (e.g. setup.py) would be better.
script_dir = os.path.dirname(os.path.abspath(__file__))
# Ensure the 'src' directory relative to the script is prioritized.
# This handles running the script from its own directory or if it's on PATH.
sys.path.insert(0, os.path.join(script_dir, 'src'))

# Fallback for running from project root (e.g., `python nmap_parallel_scanner.py`)
# where `src` is a direct subdirectory of the current working directory.
# Check if the src path relative to script dir actually has key modules.
# If not, and a 'src' dir exists in CWD, add CWD to path.
# This is a bit heuristic; a proper package structure is better.
try:
    import ip_handler # Try importing a module expected to be in src
except ImportError:
    # If the above fails, it means src is not directly under script_dir in sys.path effectively
    # or src is not a package. Try adding current working directory if src/ip_handler.py exists there.
    if os.path.exists(os.path.join(os.getcwd(), 'src', 'ip_handler.py')):
        sys.path.insert(0, os.getcwd()) # Add current dir, so 'from src.ip_handler' works
    else:
        # If it's still not found, there's a problem with where the script is
        # or where 'src' is. Print an error and exit.
        print("Error: Could not find the 'src' directory or its modules.", file=sys.stderr)
        print("Please ensure 'nmap_parallel_scanner.py' is in the project root or 'src' is in the Python path.", file=sys.stderr)
        sys.exit(1)


from src.ip_handler import read_ips_from_file, chunk_ips # Now should work with src prefix
from src.parallel_scanner import scan_chunks_parallel
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
        help="Prefix for output file names (e.g., 'scan_results/security_audit_q1').\nDirectory will be created if it doesn't exist."
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

    # Determine number of processes
    if args.num_processes is None:
        try:
            num_cpus = cpu_count()
            args.num_processes = num_cpus if num_cpus else 1
            if not num_cpus:
                 print("Warning: Could not determine number of CPU cores. Defaulting to 1 process.")
        except NotImplementedError:
            print("Warning: CPU count not available on this system. Defaulting to 1 process.")
            args.num_processes = 1
    elif args.num_processes <= 0:
        print("Warning: --num-processes must be greater than 0. Defaulting to 1 process.")
        args.num_processes = 1

    # Prepare output directory
    output_dir = os.path.dirname(args.output_prefix)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True) # exist_ok=True is helpful
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error creating output directory '{output_dir}': {e}. Files will be saved in the current directory using the full prefix.")
            # If dir creation fails, files will be saved with prefix in current dir.
            # This might mean output_prefix becomes just the filename prefix part.
            output_dir = "" # Reset output_dir so files are created in CWD with full prefix.
            # args.output_prefix remains as is, to be used as prefix.

    print(f"Starting Nmap Parallel Scanner with the following settings:")
    print(f"  Input file:      {args.input_file}")
    print(f"  Output prefix:   {os.path.abspath(args.output_prefix)}") # Show absolute path for clarity
    print(f"  Output formats:  {args.formats}")
    print(f"  Chunk size:      {args.chunk_size}")
    print(f"  Num processes:   {args.num_processes}")
    print(f"  Nmap options:    '{args.nmap_options}'") # Quoted for clarity
    print("-" * 40)

    # 1. Read IPs
    print(f"Step 1/5: Reading IPs from '{args.input_file}'...")
    ips_to_scan = read_ips_from_file(args.input_file)
    if not ips_to_scan:
        return # read_ips_from_file prints its own error
    print(f"          Found {len(ips_to_scan)} IP(s)/range(s).")

    # 2. Chunk IPs
    print(f"Step 2/5: Chunking IPs into groups of {args.chunk_size}...")
    ip_chunks = chunk_ips(ips_to_scan, chunk_size=args.chunk_size, custom_ranges=None)
    if not ip_chunks:
        print("          No IP chunks to scan (input list might have been empty after processing). Exiting.")
        return
    print(f"          Created {len(ip_chunks)} chunk(s).")

    # 3. Run scans in parallel
    print(f"Step 3/5: Starting Nmap scans for {len(ip_chunks)} chunk(s) using {args.num_processes} parallel process(es)...")
    print(f"          Nmap options for scan: '{args.nmap_options}'")
    raw_scan_results = scan_chunks_parallel(ip_chunks, args.nmap_options, args.num_processes)

    if not raw_scan_results:
        print("          Parallel scanning returned no results. This might indicate an issue with the parallel processing setup or that all scan jobs failed very early. Exiting.")
        return

    all_failed = all(isinstance(r, dict) and r.get("error") for r in raw_scan_results)
    if all_failed:
        print("          Warning: All scan chunks resulted in errors. Nmap might not be installed or accessible by subprocesses, or options might be invalid.")
    else:
        print("          Parallel scanning phase complete.")

    # 4. Consolidate results
    print("Step 4/5: Consolidating scan results...")
    consolidated_data = consolidate_scan_results(raw_scan_results)

    # Display new scan management information
    stats = consolidated_data.get("stats", {})
    print("\n--- Scan Coverage & Status ---")
    print(f"  Total unique IPs/targets provided:         {len(stats.get('all_intended_ips', []))}")
    # Uncomment to list all intended IPs if desired, can be very long.
    # print(f"    Intended IPs: {stats.get('all_intended_ips', [])}")
    print(f"  IPs with scan data (hosts found):        {len(stats.get('successfully_scanned_ips', []))}")
    # print(f"    Successfully Scanned IPs: {stats.get('successfully_scanned_ips', [])}")

    unscanned_or_error_ips = stats.get('unscanned_or_error_ips', [])
    print(f"  IPs without scan data (down/filtered/error): {len(unscanned_or_error_ips)}")
    if unscanned_or_error_ips: # Only print the list if it's not too long, or a sample
        if len(unscanned_or_error_ips) < 20 : # Arbitrary limit for direct printing
             print(f"    Unscanned/Error IPs: {unscanned_or_error_ips}")
        else:
             print(f"    Unscanned/Error IPs: List too long to display here (see output files for details).")
        # print("      (These IPs were targeted but no scan data was retrieved. They might have been down, filtered, or part of a failed scan chunk.)")

    ips_in_failed_chunks = stats.get('ips_in_failed_chunks', [])
    print(f"  IPs from chunks with execution errors:   {len(ips_in_failed_chunks)}")
    if ips_in_failed_chunks: # Only print if there are any
        if len(ips_in_failed_chunks) < 20:
            print(f"    IPs in Failed Chunks: {ips_in_failed_chunks}")
        else:
            print(f"    IPs in Failed Chunks: List too long to display here (see output files for details).")
        # print("      (The Nmap scan command itself failed for chunks containing these IPs.)")
    print("---")

    if not consolidated_data.get("hosts") and consolidated_data.get("errors"):
        print("          Consolidation: No responsive hosts found, and errors were reported during some scan chunks.")
    elif not consolidated_data.get("hosts"):
        print("          Consolidation: No responsive hosts found, or no data retrieved from scans that identified live hosts/ports.")
    else:
        print(f"          Consolidation: Found data for {len(consolidated_data.get('hosts', {}))} unique host(s) with details.")

    # 5. Save results in specified formats
    print(f"\nStep 5/5: Saving results to files with prefix '{args.output_prefix}'...")
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
