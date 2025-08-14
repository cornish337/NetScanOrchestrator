import xml.etree.ElementTree as ET
from typing import Dict, Any, List

def parse_nmap_xml(xml_string: str) -> Dict[str, Any]:
    """
    Parses Nmap XML output string and extracts key information for a single host.

    Args:
        xml_string: A string containing the XML output from an Nmap scan for one host.

    Returns:
        A dictionary with structured data about the scanned host.
        Returns an empty dictionary if parsing fails or no host data is found.
    """
    if not xml_string:
        return {"error": "Empty XML input"}

    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        return {"error": "XML parse error", "details": str(e)}

    host_element = root.find('host')
    if host_element is None:
        # Check for pre-scan info, like "host down" status
        runstats = root.find('runstats')
        if runstats is not None:
            finished = runstats.find('finished')
            if finished is not None and finished.get('summary') and '0 hosts up' in finished.get('summary', ''):
                 return {"status": {"state": "down", "reason": "no-response"}}
        return {"error": "No host element found in XML"}

    host_info: Dict[str, Any] = {
        "status": {},
        "hostnames": [],
        "addresses": {},
        "ports": []
    }

    # --- Status ---
    status_element = host_element.find('status')
    if status_element is not None:
        host_info["status"] = {
            "state": status_element.get("state", "unknown"),
            "reason": status_element.get("reason", "N/A"),
        }

    # --- Addresses ---
    address_elements = host_element.findall('address')
    for addr in address_elements:
        addr_type = addr.get("addrtype")
        if addr_type:
            host_info["addresses"][addr_type] = addr.get("addr")

    # --- Hostnames ---
    hostnames_element = host_element.find('hostnames')
    if hostnames_element is not None:
        hostname_elements = hostnames_element.findall('hostname')
        for hn in hostname_elements:
            host_info["hostnames"].append({
                "name": hn.get("name"),
                "type": hn.get("type"),
            })

    # --- Ports ---
    ports_element = host_element.find('ports')
    if ports_element is not None:
        port_elements = ports_element.findall('port')
        for port in port_elements:
            port_info: Dict[str, Any] = {
                "protocol": port.get("protocol"),
                "portid": port.get("portid"),
            }
            state_element = port.find('state')
            if state_element is not None:
                port_info["state"] = state_element.get("state")
                port_info["reason"] = state_element.get("reason")

            service_element = port.find('service')
            if service_element is not None:
                port_info["service"] = service_element.get("name")
                port_info["product"] = service_element.get("product")
                port_info["version"] = service_element.get("version")
                port_info["extrainfo"] = service_element.get("extrainfo")
                cpe_elements = service_element.findall('cpe')
                port_info["cpes"] = [cpe.text for cpe in cpe_elements]

            script_elements = port.findall('script')
            if script_elements:
                port_info['scripts'] = []
                for script in script_elements:
                    port_info['scripts'].append({
                        "id": script.get("id"),
                        "output": script.get("output"),
                    })

            host_info["ports"].append(port_info)

    return host_info
