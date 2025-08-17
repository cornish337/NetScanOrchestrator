export interface Target {
  value: string;
  isPriority: boolean;
}

// Convert dotted decimal IP to a numeric representation
function ipToNum(ip: string): number {
  return ip.split('.').reduce((acc, part) => (acc << 8) + Number(part), 0);
}

// Convert numeric representation back to dotted decimal
function numToIp(num: number): string {
  return [
    (num >>> 24) & 255,
    (num >>> 16) & 255,
    (num >>> 8) & 255,
    num & 255,
  ].join('.');
}

// Expand a CIDR notation into individual IP addresses.
function expandCidr(cidr: string, limit = 1024): string[] {
  const [base, maskStr] = cidr.split('/');
  const mask = Number(maskStr);
  if (mask < 0 || mask > 32) return [cidr];

  const start = ipToNum(base);
  const size = 2 ** (32 - mask);
  if (size > limit) {
    // Avoid generating extremely large ranges; return the CIDR as is
    return [cidr];
  }
  const addresses: string[] = [];
  for (let i = 0; i < size; i++) {
    addresses.push(numToIp(start + i));
  }
  return addresses;
}

// Expand user supplied targets into an explicit list of Target objects
export function expandTargets(input: string): Target[] {
  const tokens = input
    .split(/[\s,]+/)
    .map(t => t.trim())
    .filter(Boolean);

  const targets: Target[] = [];
  for (const token of tokens) {
    if (token.includes('/')) {
      const expanded = expandCidr(token);
      expanded.forEach(addr => targets.push({ value: addr, isPriority: false }));
    } else {
      targets.push({ value: token, isPriority: false });
    }
  }
  return targets;
}

// Suggest a reasonable chunk size given the total number of targets.
export function suggestChunkSize(totalTargets: number): number {
  if (totalTargets <= 0) return 1;
  if (totalTargets <= 256) return 64;
  if (totalTargets <= 1024) return 128;
  return 256;
}
