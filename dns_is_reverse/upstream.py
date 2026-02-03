"""Upstream DNS client for fallback queries."""

import socket
from typing import Optional

import dnslib  # type: ignore


def query_upstream(upstream_ip: str, qname: str, timeout: float = 2.0) -> Optional[list[str]]:
    """Query upstream DNS server for PTR record. Returns list of PTR values or None."""
    try:
        # Create PTR query
        query = dnslib.DNSRecord.question(qname, 'PTR')
        query_data = query.pack()
        
        # Send UDP query
        sock = socket.socket(socket.AF_INET6 if ':' in upstream_ip else socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        try:
            sock.sendto(query_data, (upstream_ip, 53))
            response_data, _ = sock.recvfrom(4096)
        finally:
            sock.close()
        
        # Parse response
        response = dnslib.DNSRecord.parse(response_data)
        
        # Check for NOERROR with answers
        if response.header.rcode == dnslib.RCODE.NOERROR and response.rr:
            ptr_values = []
            for rr in response.rr:
                if rr.rtype == dnslib.QTYPE.PTR:
                    # Strip trailing dot from PTR response
                    ptr_value = str(rr.rdata).rstrip('.')
                    ptr_values.append(ptr_value)
            return ptr_values if ptr_values else None
        
        return None
        
    except Exception:
        # Timeout, network error, parse error, etc.
        return None