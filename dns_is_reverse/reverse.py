"""IPv6 reverse DNS utilities."""

import ipaddress
from typing import Optional


def ipv6_to_nibbles(addr: ipaddress.IPv6Address) -> str:
    """Convert IPv6 address to nibble format (32 hex chars)."""
    # Get 128-bit integer, format as 32 hex chars
    return f"{int(addr):032x}"


def nibbles_to_ipv6(nibbles: str) -> ipaddress.IPv6Address:
    """Convert 32 hex nibbles to IPv6 address."""
    if len(nibbles) != 32:
        raise ValueError(f"Expected 32 nibbles, got {len(nibbles)}")
    return ipaddress.IPv6Address(int(nibbles, 16))


def ptr_qname_to_ipv6(qname: str) -> Optional[ipaddress.IPv6Address]:
    """Convert PTR qname (ip6.arpa format) to IPv6 address."""
    # Remove trailing dot and .ip6.arpa suffix
    qname = qname.rstrip('.')
    if not qname.endswith('.ip6.arpa'):
        return None
    
    nibble_part = qname[:-9]  # Remove .ip6.arpa
    nibbles = nibble_part.split('.')
    
    if len(nibbles) != 32:
        return None
    
    # Reverse nibbles and join
    try:
        hex_str = ''.join(reversed(nibbles))
        return nibbles_to_ipv6(hex_str)
    except ValueError:
        return None


def ipv6_to_ptr_qname(addr: ipaddress.IPv6Address) -> str:
    """Convert IPv6 address to PTR qname."""
    nibbles = ipv6_to_nibbles(addr)
    # Reverse nibbles and join with dots
    reversed_nibbles = '.'.join(reversed(nibbles))
    return f"{reversed_nibbles}.ip6.arpa"


def extract_host_digits(addr: ipaddress.IPv6Address, network: ipaddress.IPv6Network) -> str:
    """Extract host portion digits from IPv6 address in network."""
    if addr not in network:
        raise ValueError(f"Address {addr} not in network {network}")
    
    host_bits = 128 - network.prefixlen
    digits_len = host_bits // 4
    
    # Get host portion by XORing with network address
    host_int = int(addr) ^ int(network.network_address)
    return f"{host_int:0{digits_len}x}"


def digits_to_ipv6(digits: str, network: ipaddress.IPv6Network) -> ipaddress.IPv6Address:
    """Convert hex digits to IPv6 address in network."""
    host_bits = 128 - network.prefixlen
    expected_len = host_bits // 4
    
    if len(digits) != expected_len:
        raise ValueError(f"Expected {expected_len} digits for /{network.prefixlen}, got {len(digits)}")
    
    try:
        host_int = int(digits, 16)
    except ValueError:
        raise ValueError(f"Invalid hex digits: {digits}")
    
    addr_int = int(network.network_address) | host_int
    return ipaddress.IPv6Address(addr_int)