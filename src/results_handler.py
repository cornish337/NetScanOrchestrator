import json
import csv
from typing import List, Dict, Any
import json
import csv
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom # For pretty printing
from typing import List, Dict, Any

def consolidate_scan_results(scan_results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Consolidates a list of Nmap scan results (from multiple chunks) into a single dictionary.

    Args:
        scan_results_list: A list of dictionaries, where each dictionary is the
                           result of an Nmap scan for a chunk (from run_nmap_scan).

    Returns:
        A dictionary containing consolidated scan data, including all scanned hosts,
        their details, and any errors encountered during scans.
    """
    consolidated: Dict[str, Any] = {
        "hosts": {}, # Keyed by IP address
        "errors": [],
        "stats": {
            "total_chunks": len(scan_results_list),
            "successful_chunks": 0,
            "failed_chunks": 0,
            "total_hosts_processed_in_chunks": 0, # Sum of 'totalhosts' from scanstats if available
            "total_hosts_up_in_chunks": 0, # Sum of 'uphosts' from scanstats
            "individual_chunk_reports": [] # To store messages like "all hosts down"
        }
    }

    for i, result_chunk in enumerate(scan_results_list):
        chunk_report_summary = {"chunk_index": i}

        if result_chunk.get("error"):
            # This is for errors from run_nmap_scan or parallel_scanner itself
            error_detail = {
                "type": "scan_execution_error",
                "chunk_index": i,
                "error_message": result_chunk.get("error"),
                "details": result_chunk.get("details")
            }
            consolidated["errors"].append(error_detail)
            consolidated["stats"]["failed_chunks"] += 1
            chunk_report_summary["status"] = "failed"
            chunk_report_summary["error"] = result_chunk.get("error")
            consolidated["stats"]["individual_chunk_reports"].append(chunk_report_summary)
            continue

        consolidated["stats"]["successful_chunks"] += 1
        chunk_report_summary["status"] = "successful"

        # The structure of `result_chunk` is typically what nmap.PortScanner().scan() returns
        # e.g., {'nmap': {...}, 'scan': {'127.0.0.1': {...}, ...}, 'command_line': '...', ...}
        # It can also be our custom error dict or status dict for "all hosts down".

        scan_data = result_chunk.get('scan', {}) # This is the main dictionary of host results

        # Handle cases from run_nmap_scan where scan ran but no hosts were up / no data
        if result_chunk.get("status") == "completed" and "message" in result_chunk:
            chunk_report_summary["message"] = result_chunk["message"]
            # Store this information, as scan_data might be empty
            # Example: "All specified hosts are down or did not respond."

        if not scan_data and not result_chunk.get("error"):
             # This means the 'scan' dict was empty, but no explicit "error" key from run_nmap_scan
             # Could be due to all hosts down, or specific nmap options.
             # The message from run_nmap_scan (if any) is already added to chunk_report_summary.
             pass


        for host_ip, host_data in scan_data.items():
            if host_ip not in consolidated["hosts"]:
                consolidated["hosts"][host_ip] = host_data
            else:
                # Simple merge: update existing host_data.
                # More sophisticated merging might be needed if scans on the same host
                # were run with different options across chunks (not typical for this tool's design).
                # For now, update should be fine, assuming host_data is comprehensive for that host.
                consolidated["hosts"][host_ip].update(host_data)

        # Aggregate stats from nmap.scanstats() if present in the result chunk
        # (as returned by our modified run_nmap_scan)
        chunk_scan_stats = result_chunk.get('stats', {}) # This 'stats' is from nmap's scanstats
        if chunk_scan_stats:
            chunk_report_summary["scanstats"] = chunk_scan_stats
            try:
                consolidated["stats"]["total_hosts_processed_in_chunks"] += int(chunk_scan_stats.get('totalhosts', '0'))
                consolidated["stats"]["total_hosts_up_in_chunks"] += int(chunk_scan_stats.get('uphosts', '0'))
            except ValueError:
                print(f"Warning: Could not parse scanstats numbers for chunk {i}: {chunk_scan_stats}")

        # Add command line if present
        if 'command_line' in result_chunk.get('nmap', {}):
            chunk_report_summary["command_line"] = result_chunk['nmap']['command_line']
        elif 'command_line' in result_chunk: # if directly in result
             chunk_report_summary["command_line"] = result_chunk['command_line']


        consolidated["stats"]["individual_chunk_reports"].append(chunk_report_summary)

    # Final derived stats
    consolidated["stats"]["total_unique_hosts_found"] = len(consolidated["hosts"])

    return consolidated

# Placeholder for output functions
def to_json(consolidated_data: Dict[str, Any], output_filepath: str) -> None:
    """Saves consolidated data to a JSON file."""
    try:
        with open(output_filepath, 'w') as f:
            json.dump(consolidated_data, f, indent=4)
        print(f"Results saved to JSON: {output_filepath}")
    except IOError as e:
        print(f"Error saving JSON to {output_filepath}: {e}")

def to_csv(consolidated_data: Dict[str, Any], output_filepath: str) -> None:
    """Saves consolidated scan data to a CSV file, focusing on port details."""
    fieldnames = [
        "Host_IP", "Hostname", "Protocol", "Port_ID", "State",
        "Service_Name", "Product", "Version", "ExtraInfo", "Reason", "CPE"
    ]

    rows = []
    for ip, host_data in consolidated_data.get("hosts", {}).items():
        # Get the first hostname if available, otherwise use an empty string
        hostname = ""
        if host_data.get("hostnames"):
            # hostnames is a list of dicts, e.g., [{'name': 'example.com', 'type': 'PTR'}]
            first_hostname_entry = host_data["hostnames"][0]
            if isinstance(first_hostname_entry, dict) and "name" in first_hostname_entry:
                hostname = first_hostname_entry.get("name", "")

        # Iterate through protocols found in host_data (e.g., 'tcp', 'udp', 'ip', 'sctp')
        for proto_key in ['tcp', 'udp', 'sctp', 'ip']: # Common protocols
            if proto_key in host_data:
                ports_data = host_data[proto_key]
                if not isinstance(ports_data, dict): # Ensure ports_data is a dictionary of ports
                    continue
                for port_id, port_details in ports_data.items():
                    if not isinstance(port_details, dict): # Ensure port_details is a dictionary
                        continue
                    rows.append({
                        "Host_IP": ip,
                        "Hostname": hostname,
                        "Protocol": proto_key,
                        "Port_ID": port_id,
                        "State": port_details.get("state", ""),
                        "Service_Name": port_details.get("name", ""),
                        "Product": port_details.get("product", ""),
                        "Version": port_details.get("version", ""),
                        "ExtraInfo": port_details.get("extrainfo", ""),
                        "Reason": port_details.get("reason", ""),
                        "CPE": port_details.get("cpe", "")
                    })

    if not rows:
        print("No detailed port data to write to CSV. Creating CSV with headers only.")
        # Create an empty CSV with headers or skip file creation
        try:
            with open(output_filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            print(f"Empty CSV report saved to {output_filepath}")
        except IOError as e:
            print(f"Error writing empty CSV to {output_filepath}: {e}")
        return

    try:
        with open(output_filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"CSV report saved to {output_filepath}")
    except IOError as e:
        print(f"Error writing CSV to {output_filepath}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CSV generation: {e}")

def _dict_to_xml_element(tag_name: str, data: Dict[str, Any]) -> ET.Element:
    """Helper to convert simple dict to an XML element with subelements for non-nested dicts."""
    elem = ET.Element(tag_name)
    for key, value in data.items():
        child = ET.Element(key.replace(" ", "_").replace("(", "").replace(")", "")) # Sanitize tag names
        # If value is a list (like individual_chunk_reports), serialize it or skip
        if isinstance(value, list):
            # For simplicity, convert list to a string or create sub-elements for each item
            # Here, we'll convert to string; a more complex handling might be needed for structured lists
            try:
                child.text = json.dumps(value) # Serialize list as JSON string
            except TypeError: # Handle non-serializable list content
                child.text = "List content not directly serializable to XML text"

            # Alternative: create sub-elements for each item in the list
            # for idx, item in enumerate(value):
            #    item_elem = ET.Element(f"{key}_item_{idx}")
            #    item_elem.text = str(item) # Or recursively call _dict_to_xml_element if item is dict
            #    child.append(item_elem)
        else:
            child.text = str(value)
        elem.append(child)
    return elem

def to_xml(consolidated_data: Dict[str, Any], output_filepath: str) -> None:
    """Saves consolidated scan data to a custom XML file."""
    root = ET.Element("scan_results")

    # Stats
    # The stats dict can have nested structures like 'individual_chunk_reports' (list of dicts)
    # _dict_to_xml_element is too simple for that. We'll handle stats more manually.
    if "stats" in consolidated_data:
        stats_data = consolidated_data["stats"]
        stats_elem = ET.Element("stats")
        for key, value in stats_data.items():
            if key == "individual_chunk_reports" and isinstance(value, list):
                reports_elem = ET.Element("individual_chunk_reports")
                for report_item in value:
                    if isinstance(report_item, dict):
                        report_elem = _dict_to_xml_element("chunk_report", report_item)
                        reports_elem.append(report_elem)
                stats_elem.append(reports_elem)
            else:
                child = ET.Element(key.replace(" ", "_").replace("(", "").replace(")", ""))
                child.text = str(value)
                stats_elem.append(child)
        root.append(stats_elem)


    # Hosts
    hosts_elem = ET.Element("hosts")
    for ip, host_data in consolidated_data.get("hosts", {}).items():
        host_elem = ET.Element("host")
        host_elem.set("ip", ip)

        # Hostnames
        if host_data.get("hostnames") and isinstance(host_data["hostnames"], list):
            hostnames_elem = ET.Element("hostnames")
            for hn_entry in host_data["hostnames"]:
                if isinstance(hn_entry, dict) and hn_entry.get("name"):
                    hn_elem = ET.Element("hostname")
                    hn_elem.set("name", hn_entry["name"])
                    hn_elem.set("type", hn_entry.get("type", ""))
                    hostnames_elem.append(hn_elem)
            if list(hostnames_elem):
                 host_elem.append(hostnames_elem)

        # Status
        if host_data.get("status") and isinstance(host_data["status"], dict):
            status_elem = ET.Element("status")
            status_elem.set("state", host_data["status"].get("state", ""))
            status_elem.set("reason", host_data["status"].get("reason", ""))
            host_elem.append(status_elem)

        # Protocols (tcp, udp, etc.) and their Ports
        # Nmap output has specific protocol keys like 'tcp', 'udp'
        ports_root_elem = ET.Element("ports") # Changed from "protocols" to "ports" for clarity
        for proto_key in ['tcp', 'udp', 'sctp', 'ip']: # Iterate common protocols
            if proto_key in host_data and isinstance(host_data[proto_key], dict):
                proto_elem = ET.Element(proto_key) # e.g., <tcp>
                ports_dict = host_data[proto_key]
                for port_id, port_details in ports_dict.items():
                    if not isinstance(port_details, dict): continue

                    port_elem = ET.Element("port")
                    port_elem.set("portid", str(port_id))

                    # State of the port
                    state_elem = ET.Element("state")
                    state_elem.set("state", port_details.get("state", ""))
                    state_elem.set("reason", port_details.get("reason", ""))
                    port_elem.append(state_elem)

                    # Service information
                    service_elem = ET.Element("service")
                    service_elem.set("name", port_details.get("name", ""))
                    service_elem.set("product", port_details.get("product", ""))
                    service_elem.set("version", port_details.get("version", ""))
                    service_elem.set("extrainfo", port_details.get("extrainfo", ""))
                    service_elem.set("cpe", port_details.get("cpe", ""))
                    # Add other service details if needed, e.g., ostype, method, conf
                    if port_details.get('ostype'):
                        service_elem.set("ostype", port_details.get('ostype',''))
                    if port_details.get('method'):
                        service_elem.set("method", port_details.get('method',''))
                    if port_details.get('conf'):
                        service_elem.set("conf", str(port_details.get('conf','')))

                    port_elem.append(service_elem)
                    proto_elem.append(port_elem)
                if list(proto_elem): # Only append if there were ports for this protocol
                    ports_root_elem.append(proto_elem)

        if list(ports_root_elem):
            host_elem.append(ports_root_elem)

        hosts_elem.append(host_elem)

    if list(hosts_elem):
        root.append(hosts_elem)

    # Errors
    if consolidated_data.get("errors"):
        errors_elem = ET.Element("errors")
        for error_report in consolidated_data["errors"]:
            error_elem = ET.Element("error_item") # Changed tag to be more specific
            if isinstance(error_report, dict):
                 # Use _dict_to_xml_element for consistent error structure
                 # error_elem = _dict_to_xml_element("error_report", error_report)
                 # Or manually:
                 error_elem.set("type", error_report.get("type", "Unknown"))
                 error_elem.set("chunk_index", str(error_report.get("chunk_index", "")))
                 ET.SubElement(error_elem, "message").text = error_report.get("error_message", "N/A")
                 ET.SubElement(error_elem, "details").text = str(error_report.get("details", ""))
            else:
                 error_elem.text = str(error_report) # Fallback for simple string errors
            errors_elem.append(error_elem)
        if list(errors_elem):
            root.append(errors_elem)

    # Pretty print XML
    xml_str = ET.tostring(root, encoding="unicode")
    try:
        dom = minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent="  ")

        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(pretty_xml_str)
        print(f"XML report saved to {output_filepath}")
    except IOError as e:
        print(f"Error writing XML to {output_filepath}: {e}")
    except Exception as parse_err:
        print(f"Error generating pretty XML (falling back to raw string): {parse_err}")
        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(xml_str) # Write the non-prettified string
            print(f"XML report (raw) saved to {output_filepath}")
        except IOError as e_raw:
             print(f"Error writing raw XML to {output_filepath}: {e_raw}")


def to_txt(consolidated_data: Dict[str, Any], output_filepath: str) -> None:
    """Saves a human-readable summary of scan results to a TXT file."""
    lines = []

    # Overall Stats
    lines.append("--- Scan Summary ---")
    stats = consolidated_data.get("stats", {})
    for key, value in stats.items():
        if key == "individual_chunk_reports": # Skip verbose individual reports for main summary
            lines.append(f"{key.replace('_', ' ').title()}: {len(value)} reports (see details below or in JSON if needed)")
            continue
        lines.append(f"{key.replace('_', ' ').title()}: {value}")

    # Individual Chunk Reports Summary (optional, could be verbose)
    # lines.append("\n--- Chunk Processing Details ---")
    # for report in stats.get("individual_chunk_reports", []):
    #     lines.append(f"  Chunk {report.get('chunk_index')}: Status: {report.get('status')}")
    #     if report.get('message'):
    #         lines.append(f"    Message: {report.get('message')}")
    #     if report.get('error'):
    #         lines.append(f"    Error: {report.get('error')}")
    #     if report.get('scanstats'):
    #         lines.append(f"    Scanstats: Up: {report['scanstats'].get('uphosts', 'N/A')}, Down: {report['scanstats'].get('downhosts', 'N/A')}, Total: {report['scanstats'].get('totalhosts', 'N/A')}")


    lines.append("\n--- Hosts ---")
    hosts_found = consolidated_data.get("hosts", {})
    if not hosts_found:
        lines.append("No hosts found with open ports or specific details to report.")
    else:
        for ip, host_data in hosts_found.items():
            lines.append(f"\nHost: {ip}")

            # Hostnames
            hostnames_list = host_data.get("hostnames", [])
            if hostnames_list:
                # Typically, hostnames_list is like [{'name': 'hostname1', 'type': 'A'}, {'name': 'hostname2', 'type': 'PTR'}]
                names = [hn.get("name", "") for hn in hostnames_list if isinstance(hn, dict) and hn.get("name")]
                types = [hn.get("type", "") for hn in hostnames_list if isinstance(hn, dict) and hn.get("type")]
                if names:
                    lines.append(f"  Hostname(s): {', '.join(names)} ({', '.join(types)})")

            # Status (up, down)
            status_info = host_data.get("status", {})
            if isinstance(status_info, dict):
                 lines.append(f"  State: {status_info.get('state', 'unknown')} (Reason: {status_info.get('reason', 'N/A')})")

            # Protocols and Ports
            processed_ports_for_host = False
            for proto_key in ['tcp', 'udp', 'sctp', 'ip']: # Iterate common protocols
                if proto_key in host_data:
                    ports_data = host_data[proto_key]
                    if isinstance(ports_data, dict) and ports_data: # Check if there are ports for this protocol
                        lines.append(f"  Protocol: {proto_key.upper()}")
                        processed_ports_for_host = True
                        for port_id, port_details in ports_data.items():
                            if not isinstance(port_details, dict): continue # Skip if port_details is not a dict

                            details_parts = [f"Port: {port_id}", f"State: {port_details.get('state', '')}"]
                            if port_details.get('name'):
                                details_parts.append(f"Service: {port_details.get('name', '')}")
                            if port_details.get('product'):
                                product_info = port_details.get('product', '')
                                if port_details.get('version'):
                                    product_info += f" version {port_details.get('version', '')}"
                                details_parts.append(f"Product: {product_info}")
                            if port_details.get('extrainfo'):
                                details_parts.append(f"ExtraInfo: {port_details.get('extrainfo', '')}")
                            if port_details.get('reason'):
                                details_parts.append(f"Reason: {port_details.get('reason', '')}")
                            lines.append(f"    {' | '.join(details_parts)}")
                        if not ports_data: # No ports listed under this protocol for this host
                            lines.append(f"    No open ports found or scanned for {proto_key.upper()}.")
            if not processed_ports_for_host and status_info.get('state') == 'up':
                 lines.append("  No open ports found or scanned for this host (or host did not respond to port scan probes).")
            elif status_info.get('state') != 'up':
                 lines.append("  Host is not up, or did not respond to probes.")


    # Errors encountered during scans
    errors_list = consolidated_data.get("errors", [])
    if errors_list:
        lines.append("\n--- Errors & Issues ---")
        for error_report in errors_list:
            line = f"Type: {error_report.get('type', 'N/A')}, Chunk: {error_report.get('chunk_index', 'N/A')}, Message: {error_report.get('error_message', 'Unknown error')}"
            if error_report.get('details'):
                line += f" - Details: {error_report.get('details')}"
            lines.append(line)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as txtfile: # Added encoding
            for line in lines:
                txtfile.write(line + os.linesep)
        print(f"TXT report saved to {output_filepath}")
    except IOError as e:
        print(f"Error writing TXT to {output_filepath}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during TXT generation: {e}")


def to_markdown(consolidated_data: Dict[str, Any], output_filepath: str) -> None:
    """Saves a summary of consolidated data to a Markdown file."""
    # This will be a more structured version of the TXT report.
    lines = []

    # Overall Stats
    lines.append("# Scan Report Summary")
    lines.append("## Overall Statistics")
    stats = consolidated_data.get("stats", {})
    for key, value in stats.items():
        if key == "individual_chunk_reports":
            lines.append(f"- **{key.replace('_', ' ').title()}:** {len(value)} reports (details omitted for brevity in Markdown summary)")
            continue
        lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")

    lines.append("\n## Hosts Details")
    hosts_found = consolidated_data.get("hosts", {})
    if not hosts_found:
        lines.append("\nNo hosts found with open ports or specific details to report.")
    else:
        for ip, host_data in hosts_found.items():
            lines.append(f"\n### Host: `{ip}`")

            hostnames_list = host_data.get("hostnames", [])
            if hostnames_list:
                names = [hn.get("name", "") for hn in hostnames_list if isinstance(hn, dict) and hn.get("name")]
                if names:
                    lines.append(f"- **Hostname(s):** {', '.join(names)}")

            status_info = host_data.get("status", {})
            if isinstance(status_info, dict):
                 lines.append(f"- **State:** {status_info.get('state', 'unknown')} (Reason: {status_info.get('reason', 'N/A')})")

            processed_ports_for_host = False
            for proto_key in ['tcp', 'udp', 'sctp', 'ip']:
                if proto_key in host_data:
                    ports_data = host_data[proto_key]
                    if isinstance(ports_data, dict) and ports_data:
                        lines.append(f"- **Protocol: {proto_key.upper()}**")
                        processed_ports_for_host = True
                        lines.append("  | Port | State | Service | Product & Version | ExtraInfo | Reason |")
                        lines.append("  |------|-------|---------|-------------------|-----------|--------|")
                        for port_id, port_details in ports_data.items():
                            if not isinstance(port_details, dict): continue

                            product_info = port_details.get('product', '')
                            if port_details.get('version'):
                                product_info += f" {port_details.get('version', '')}"

                            lines.append(f"  | {port_id} "
                                         f"| {port_details.get('state', '')} "
                                         f"| {port_details.get('name', '')} "
                                         f"| {product_info} "
                                         f"| {port_details.get('extrainfo', '')} "
                                         f"| {port_details.get('reason', '')} |")
                        if not ports_data:
                             lines.append(f"  No open ports found or scanned for {proto_key.upper()}.")

            if not processed_ports_for_host and status_info.get('state') == 'up':
                 lines.append("- No open ports found or scanned for this host (or host did not respond to port scan probes).")
            elif status_info.get('state') != 'up' and not processed_ports_for_host :
                 lines.append("- Host is not up, or did not respond to probes.")


    errors_list = consolidated_data.get("errors", [])
    if errors_list:
        lines.append("\n## Errors & Issues")
        lines.append("| Chunk Index | Type | Error Message | Details |")
        lines.append("|-------------|------|---------------|---------|")
        for error_report in errors_list:
            lines.append(f"| {error_report.get('chunk_index', 'N/A')} "
                         f"| {error_report.get('type', 'N/A')} "
                         f"| {error_report.get('error_message', 'Unknown error')} "
                         f"| {error_report.get('details', '')} |")

    try:
        with open(output_filepath, 'w', encoding='utf-8') as mdfile:
            for line in lines:
                mdfile.write(line + os.linesep)
        print(f"Markdown report saved to {output_filepath}")
    except IOError as e:
        print(f"Error writing Markdown to {output_filepath}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during Markdown generation: {e}")

# Example of how one might add more detailed CSV later:
# def generate_csv_rows(consolidated_data: Dict[str, Any]) -> List[Dict[str, str]]:
# (as shown commented out in to_csv)
# ...
