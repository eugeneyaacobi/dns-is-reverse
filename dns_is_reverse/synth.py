"""DNS record synthesis utilities."""

import ipaddress
import re
from typing import Optional, Tuple

from .config import NetworkConfig
from .reverse import extract_host_digits, digits_to_ipv6


def synthesize_ptr_hostname(addr: ipaddress.IPv6Address, network_config: NetworkConfig) -> str:
    """Synthesize PTR hostname from IPv6 address."""
    digits = extract_host_digits(addr, network_config.network)
    return network_config.template.replace('%DIGITS%', digits)


def parse_aaaa_hostname(hostname: str, network_config: NetworkConfig) -> Optional[str]:
    """Extract digits from hostname using template. Returns None if no match."""
    # Escape template and replace %DIGITS% with capture group
    escaped = re.escape(network_config.template)
    escaped_digits = re.escape('%DIGITS%')
    pattern = escaped.replace(escaped_digits, r'([0-9a-fA-F]+)')
    pattern = f"^{pattern}$"
    
    match = re.match(pattern, hostname, re.IGNORECASE)
    if not match:
        return None
    
    return match.group(1).lower()


def synthesize_aaaa_address(hostname: str, network_config: NetworkConfig) -> Optional[ipaddress.IPv6Address]:
    """Synthesize IPv6 address from hostname. Returns None if hostname doesn't match template."""
    digits = parse_aaaa_hostname(hostname, network_config)
    if digits is None:
        return None
    
    try:
        return digits_to_ipv6(digits, network_config.network)
    except ValueError:
        return None


def find_matching_network(addr: ipaddress.IPv6Address, networks: list[NetworkConfig]) -> Optional[NetworkConfig]:
    """Find network config that contains the given address."""
    for network_config in networks:
        if addr in network_config.network:
            return network_config
    return None


def find_matching_template(hostname: str, networks: list[NetworkConfig]) -> Optional[NetworkConfig]:
    """Find network config whose template matches the hostname."""
    for network_config in networks:
        if parse_aaaa_hostname(hostname, network_config) is not None:
            return network_config
    return None