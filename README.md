# DNS-is-reverse

A Python reimplementation of [all-knowing-dns](https://github.com/raumzeitlabor/all-knowing-dns): a tiny authoritative DNS server that synthesizes IPv6 reverse DNS (PTR) and matching forward AAAA records on the fly for SLAAC-style networks, avoiding gigantic zone files.

## What it does

DNS-is-reverse answers DNS queries for IPv6 networks by synthesizing responses based on templates:

- **PTR queries**: For reverse DNS lookups (ip6.arpa), it extracts the host portion of the IPv6 address and generates a hostname using a configurable template
- **AAAA queries**: For forward DNS lookups, it parses hostnames matching the template and returns the corresponding IPv6 address within the configured network
- **Upstream fallback**: For PTR queries, it can optionally query an upstream DNS server first before synthesizing locally

## Configuration Format

The configuration file uses a simple line-based format:

```
listen <address>
network <CIDR>
    resolves to <template>
    with upstream <address>  # optional
```

### Example Configuration

```
# Listen on IPv6 and IPv4
listen ::1
listen 127.0.0.1

# Configure a /64 network
network 2001:4d88:100e:ccc0::/64
    resolves to ipv6-%DIGITS%.nutzer.raumzeitlabor.de
    with upstream 2001:4860:4860::8888

# Configure a /56 network without upstream
network 2001:db8:100::/56
    resolves to host-%DIGITS%.example.com
```

## How %DIGITS% Works

The `%DIGITS%` placeholder in templates represents the host portion of IPv6 addresses as hexadecimal digits:

- For a `/64` network: 64 host bits = 16 hex digits
- For a `/56` network: 72 host bits = 18 hex digits  
- For a `/80` network: 48 host bits = 12 hex digits

### Example for /64 network `2001:4d88:100e:ccc0::/64`:

- IPv6 address: `2001:4d88:100e:ccc0:216:eaff:fecb:826`
- Host portion: `0216eafffecb0826` (16 hex digits, zero-padded)
- Template: `ipv6-%DIGITS%.example.com`
- Generated hostname: `ipv6-0216eafffecb0826.example.com`

## Upstream Fallback

When a network has `with upstream <address>` configured:

1. For PTR queries, DNS-is-reverse first queries the upstream server for `<original_ptr_qname>.upstream`
2. If the upstream returns a PTR answer, that answer is relayed to the client
3. If the upstream returns NXDOMAIN/timeout/no-answer, DNS-is-reverse synthesizes the response locally
4. AAAA queries are always synthesized locally (no upstream fallback)

## Installation

### Native Installation

```bash
pip install -e .
```

### Docker Installation

```bash
# Using docker-compose (recommended)
docker-compose up --build

# Or build and run manually
docker build -t dns-is-reverse .
docker run -p 53:53/udp -v ./test.conf:/etc/dns-is-reverse.conf:ro dns-is-reverse
```

## Usage

### Command Line Options

```bash
dns-is-reverse [options]

Options:
  --configfile PATH     Configuration file path (default: /etc/all-knowing-dns.conf)
  --listen ADDRESS      Additional listen address (can be used multiple times)
  --port PORT          Listen port (default: 53)
  --querylog           Enable query logging to stdout
```

### Running on High Port (Non-root)

For development or non-root usage:

```bash
dns-is-reverse --configfile ./test.conf --port 5353 --querylog
```

### Running with Docker

The Docker container runs on port 53 by default:

```bash
# Start with docker-compose
docker-compose up

# Or run directly with custom config
docker run -p 53:53/udp -v /path/to/config.conf:/etc/dns-is-reverse.conf:ro dns-is-reverse
```

### Example Configuration File

Create `test.conf`:

```
listen ::1
listen 127.0.0.1

network 2001:db8::/64
    resolves to test-%DIGITS%.local

network 2001:db8:100::/56
    resolves to server-%DIGITS%.example.com
    with upstream 8.8.8.8
```

### Testing with dig

```bash
# Test AAAA query
dig @::1 -p 5353 test-1234567890abcdef.local AAAA

# Test PTR query  
dig @::1 -p 5353 -x 2001:db8::1234:5678:9abc:def0
```

## Supported Network Sizes

DNS-is-reverse works with any IPv6 network size where the host portion is a multiple of 4 bits:

- `/64` networks: 16 hex digits (most common for SLAAC)
- `/56` networks: 18 hex digits  
- `/48` networks: 20 hex digits
- `/80` networks: 12 hex digits
- etc.

## DNS Behavior

- **Authoritative**: All synthesized responses have the AA (Authoritative Answer) flag set
- **TTL**: All responses use a 60-second TTL
- **Error handling**: Returns NXDOMAIN for out-of-network queries or template mismatches
- **Malformed queries**: Returns FORMERR for unparseable DNS requests
- **Query types**: Only PTR and AAAA queries are supported; all others return NXDOMAIN

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Type Checking

```bash
mypy dns_is_reverse/
```

## License

MIT License