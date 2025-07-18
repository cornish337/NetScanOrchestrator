import nmap
from typing import List, Dict, Any # Added typing

def run_nmap_scan(targets: List[str], options: str = "-T4 -F") -> Dict[str, Any]: # Ensure typing
    """
    Runs an Nmap scan on the given targets with the specified options.
    Includes input_targets in the returned dictionary.

    Args:
        targets: A list of IP addresses or network ranges.
        options: Nmap command-line options.

    Returns:
        A dictionary containing the parsed Nmap scan results (or error details)
        and the original list of input_targets.
    """
    nm = nmap.PortScanner()
    target_string = " ".join(targets)
    # Initialize result_dict with input_targets. This ensures it's always present.
    result_dict: Dict[str, Any] = {"input_targets": targets}

    try:
        # The scan method of python-nmap executes nmap and parses XML output.
        scan_output = nm.scan(hosts=target_string, arguments=options)

        # Merge the raw scan_output into our result_dict.
        # scan_output structure is typically {'nmap': {...}, 'scan': {host1:..., host2:...}}
        result_dict.update(scan_output)

        # Post-scan checks, modifying result_dict directly.
        # nm.all_hosts() gives a list of hosts that were scanned and had data.
        # result_dict.get('scan') is the dictionary of results per host.
        if not result_dict.get('scan'):
            # This means no hosts were found in the 'scan' part of the output.
            # Could be all down, or other Nmap issues not raising PortScannerError.
            current_scan_stats = nm.scanstats() # Get stats from the PortScanner object
            result_dict["stats"] = current_scan_stats # Always include stats if available

            if current_scan_stats.get('uphosts', '0') == '0' and \
               current_scan_stats.get('totalhosts', '0') != '0': # Check if scan ran and all were down
                 result_dict["status"] = "completed"
                 result_dict["message"] = f"All {current_scan_stats.get('totalhosts','')} specified target(s) are down or did not respond."
                 # result_dict["hosts_scanned"] = nm.all_hosts() # This would be empty
            else:
                # If 'scan' is empty but not because all hosts are down (e.g. bad options, other nmap issue)
                # and no specific error message has been set yet by an exception.
                if "error" not in result_dict:
                    result_dict["error"] = "Scan completed but produced no host data."
                    result_dict["details"] = (
                        "Targets might be invalid, filtered, Nmap options prevented data collection, "
                        "or Nmap encountered an issue not raised as a PortScannerError. "
                        f"Nmap command line: {nm.command_line()}"
                    )

    except nmap.PortScannerError as e:
        # This exception is raised if Nmap is not found or if there's an error running the command
        # (e.g., malformed arguments that nmap itself rejects).
        error_msg = f"Nmap scan error for targets '{target_string}': {str(e)}"
        print(error_msg) # Consider using logging module for real applications
        result_dict["error"] = "Nmap execution failed."
        # Provide a more specific detail if Nmap is not found.
        if "nmap program was not found" in str(e).lower():
            result_dict["details"] = "Nmap command not found. Please ensure Nmap is installed and in your system's PATH."
        elif "Error compiling our pcap filter" in str(e):
            result_dict["details"] = (
                f"Nmap pcap filter compilation error: {str(e)}. "
                "This may be due to Nmap lacking necessary permissions (e.g., root or CAP_NET_RAW) "
                "for the chosen scan type, or a conflict with other packet filtering software. "
                "Try using a TCP Connect Scan (-sT) or ensure Nmap has appropriate privileges."
            )
        else:
            result_dict["details"] = str(e)
        # Include scan stats if available even in error, though might be minimal
        if nm.scanstats():
             result_dict["stats"] = nm.scanstats()

    except Exception as e:
        # Catch any other unexpected errors during the scan process.
        error_msg = f"An unexpected error occurred during Nmap scan for targets '{target_string}': {str(e)}"
        print(error_msg) # Consider logging
        result_dict["error"] = "Unexpected error during scan."
        result_dict["details"] = str(e)
        if nm.scanstats(): # Try to get stats
             result_dict["stats"] = nm.scanstats()

    return result_dict
