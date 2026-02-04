"""Configuration file parser."""

import re
from ipaddress import IPv6Network
from typing import Iterator

from .config import Config, NetworkConfig


def parse_config(text: str) -> Config:
    """Parse configuration from text."""
    lines = [line.rstrip() for line in text.splitlines()]
    listen_addresses: list[str] = []
    networks: list[NetworkConfig] = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('#'):
            i += 1
            continue
            
        if line.startswith('listen '):
            address = line[7:].strip()
            listen_addresses.append(address)
            i += 1
        elif line.startswith('network '):
            network_str = line[8:].strip()
            network = IPv6Network(network_str)
            i += 1
            
            # Parse indented block
            template = None
            upstream = None
            
            while i < len(lines):
                if not lines[i] or lines[i].startswith('#'):
                    i += 1
                    continue
                if not lines[i].startswith((' ', '\t')):
                    break
                    
                subline = lines[i].strip()
                if subline.startswith('resolves to '):
                    template = subline[12:].strip()
                elif subline.startswith('with upstream '):
                    upstream = subline[14:].strip()
                i += 1
            
            if template is None:
                raise ValueError(f"Network {network_str} missing 'resolves to' directive")
            
            networks.append(NetworkConfig(network, template, upstream))
        else:
            raise ValueError(f"Unknown directive: {line}")
    
    if not listen_addresses:
        listen_addresses = ["::", "0.0.0.0"]
    
    return Config(listen_addresses, networks)