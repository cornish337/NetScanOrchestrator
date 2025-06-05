# Scan Report Summary
## Overall Statistics
- **Total Chunks:** 2
- **Successful Chunks:** 2
- **Failed Chunks:** 0
- **Total Input Targets Processed:** 18
- **Total Hosts Up Reported By Nmap:** 0
- **All Intended Ips:** ['# (45.33.32.156, 45.33.32.157, 45.33.32.158, 45.33.32.159)', '# A small CIDR range', '# Example IP Addresses and Ranges for Nmap Parallel Scanner', '# For a "clean" functional example, ensure only valid targets are listed without leading comments.', "# Google's Public DNS Servers", "# Hyphenated range (using a small part of Google's DNS range for safety)", '# Lines starting with # will be treated as hostnames by Nmap', '# Our current ip_handler.read_ips_from_file does not filter them.', "# Publicly scannable host (Nmap's test site)", '# This example file is intended to be clean for direct use.', "# Using scanme.nmap.org's /30 block for demonstration.", '# if not filtered by an input processing function.', '45.33.32.156/30', '8.8.4.4', '8.8.8.1-8.8.8.3', '8.8.8.8', '```', 'scanme.nmap.org']
- **Successfully Scanned Ips:** ['8.8.4.4', '8.8.8.8']
- **Ips In Failed Chunks:** []
- **Unscanned Or Error Ips:** ['# (45.33.32.156, 45.33.32.157, 45.33.32.158, 45.33.32.159)', '# A small CIDR range', '# Example IP Addresses and Ranges for Nmap Parallel Scanner', '# For a "clean" functional example, ensure only valid targets are listed without leading comments.', "# Google's Public DNS Servers", "# Hyphenated range (using a small part of Google's DNS range for safety)", '# Lines starting with # will be treated as hostnames by Nmap', '# Our current ip_handler.read_ips_from_file does not filter them.', "# Publicly scannable host (Nmap's test site)", '# This example file is intended to be clean for direct use.', "# Using scanme.nmap.org's /30 block for demonstration.", '# if not filtered by an input processing function.', '45.33.32.156/30', '8.8.8.1-8.8.8.3', '```', 'scanme.nmap.org']
- **Individual Chunk Reports:** 2 reports (details omitted for brevity in Markdown summary)
- **Total Unique Hosts Found:** 2

## Hosts Details

### Host: `8.8.8.8`
- **Hostname(s):** dns.google
- **State:** up (Reason: echo-reply)
- **Protocol: TCP**
  | Port | State | Service | Product & Version | ExtraInfo | Reason |
  |------|-------|---------|-------------------|-----------|--------|
  | 53 | open | domain |  |  | syn-ack |
  | 443 | open | https |  |  | syn-ack |

### Host: `8.8.4.4`
- **Hostname(s):** dns.google
- **State:** up (Reason: syn-ack)
- **Protocol: TCP**
  | Port | State | Service | Product & Version | ExtraInfo | Reason |
  |------|-------|---------|-------------------|-----------|--------|
  | 53 | open | domain |  |  | syn-ack |
  | 443 | open | https |  |  | syn-ack |
