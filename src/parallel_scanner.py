import multiprocessing
from typing import List, Dict

from .nmap_scanner import run_nmap_scan
# We might need to wrap run_nmap_scan or pass arguments carefully for starmap
# For now, let's assume we'll adapt the call within scan_chunks_parallel

def scan_chunks_parallel(ip_chunks: List[List[str]], nmap_options: str, num_processes: int = None) -> List[Dict]:
    """
    Scans multiple chunks of IPs in parallel using Nmap.

    Args:
        ip_chunks: A list of IP chunks (each chunk is a list of IP strings).
        nmap_options: Nmap command-line options string.
        num_processes: The number of parallel processes to use.
                       Defaults to the number of CPU cores if None.

    Returns:
        A list of dictionaries, where each dictionary is the result
        from run_nmap_scan for the corresponding chunk.
    """
    if not ip_chunks:
        return []

    if num_processes is None:
        num_processes = multiprocessing.cpu_count()

    # Ensure num_processes is not more than the number of chunks, to avoid creating idle processes
    num_processes = min(num_processes, len(ip_chunks))

    if num_processes <= 0: # Should not happen with cpu_count() but as a safeguard
        num_processes = 1

    # Create a list of arguments for each call to run_nmap_scan
    # Each item in pool_args will be a tuple (chunk, nmap_options)
    pool_args = [(chunk, nmap_options) for chunk in ip_chunks]

    results = []
    # Using try-finally to ensure pool is closed
    pool = None # Initialize pool to None
    try:
        # Set start method to 'spawn' for better compatibility across platforms if issues arise
        # ctx = multiprocessing.get_context('spawn')
        # pool = ctx.Pool(processes=num_processes)
        pool = multiprocessing.Pool(processes=num_processes)
        # Use starmap to pass multiple arguments to run_nmap_scan
        # run_nmap_scan expects (targets: list[str], options: str)
        results = pool.starmap(run_nmap_scan, pool_args)
    except Exception as e:
        print(f"Error during parallel scanning: {e}")
        # Depending on desired robustness, might return partial results or a specific error indicator
        # Create a list of error dicts matching the number of expected results
        error_result = {"error": "Parallel processing failed", "details": str(e)}
        return [error_result for _ in ip_chunks]
    finally:
        if pool:
            pool.close()
            pool.join()

    return results

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    # This requires src.ip_handler to be accessible and an example IP file
    # For now, this is a placeholder for direct module testing

    # from src.ip_handler import read_ips_from_file, chunk_ips

    # # Create a dummy ip_list.txt for testing
    # # Ensure this file is created in a writable location, e.g., /tmp or project root
    # temp_file_path = "temp_ips_for_parallel_test.txt"
    # with open(temp_file_path, "w") as f:
    #     f.write("scanme.nmap.org\n")
    #     # f.write("192.168.1.1\n") # A local IP, may not be scannable from outside or may not exist
    #     f.write("8.8.8.8\n")
    #     f.write("github.com\n")
    #     f.write("gitlab.com\n")


    # test_ips = read_ips_from_file(temp_file_path)
    # if test_ips:
    #     # Chunk size of 1 for testing, so each host is a chunk
    #     test_chunks = chunk_ips(test_ips, chunk_size=1)
    #     # test_chunks = chunk_ips(test_ips, chunk_size=2) # Or chunk size 2
    #     print(f"Test Chunks: {test_chunks}")

    #     # It's important that Nmap is installed for this test to run
    #     # and that the targets are resolvable and scannable.
    #     # Using options that are quick and less intrusive for testing.
    #     # -sn: Ping scan (no port scan). -T4: Aggressive timing.
    #     # Use -F for fast port scan if testing port scanning functionality.
    #     scan_results = scan_chunks_parallel(test_chunks, nmap_options="-sn -T4", num_processes=2)
    #     print("\nScan Results:")
    #     for i, result in enumerate(scan_results):
    #         print(f"--- Chunk {i+1} (Targets: {test_chunks[i]}) ---")
    #         if result.get("error"):
    #             print(f"  Error: {result.get('error')} - Details: {result.get('details')}")
    #         elif not result.get('scan') and result.get('status') == 'completed':
    #             print(f"  Status: {result.get('message', 'No specific message for empty scan result.')}")
    #             print(f"  Stats: {result.get('stats')}")
    #         elif not result.get('scan'):
    #             print(f"  Warning: Scan result for this chunk is empty or missing 'scan' key. Full result: {result}")
    #         else:
    #             for host, data in result.get('scan', {}).items():
    #                 host_status = data.get('status', {}).get('state', 'unknown')
    #                 print(f"  Host: {host} ({host_status})")
    #                 if host_status == 'up':
    #                     # Example: print open TCP ports if available from options like -F
    #                     for proto in data.get('tcp', {}):
    #                         port_info = data['tcp'][proto]
    #                         print(f"    Port: {proto}/tcp, State: {port_info.get('state')}, Name: {port_info.get('name')}")
    #     print(f"\nTotal chunks processed: {len(scan_results)}")

    # # Clean up dummy file
    # import os
    # try:
    #     os.remove(temp_file_path)
    # except OSError as e:
    #     print(f"Error removing temporary test file {temp_file_path}: {e}")
    pass
