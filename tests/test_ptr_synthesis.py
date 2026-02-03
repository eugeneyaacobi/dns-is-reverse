"""Tests for PTR record synthesis."""

import ipaddress
import pytest

from dns_is_reverse.config import NetworkConfig
from dns_is_reverse.synth import synthesize_ptr_hostname, find_matching_network


def test_synthesize_ptr_hostname_64():
    """Test PTR hostname synthesis for /64 network."""
    addr = ipaddress.IPv6Address("2001:4d88:100e:ccc0:216:eaff:fecb:826")
    network = ipaddress.IPv6Network("2001:4d88:100e:ccc0::/64")
    template = "ipv6-%DIGITS%.nutzer.raumzeitlabor.de"
    
    config = NetworkConfig(network, template)
    hostname = synthesize_ptr_hostname(addr, config)
    
    assert hostname == "ipv6-0216eafffecb0826.nutzer.raumzeitlabor.de"


def test_synthesize_ptr_hostname_56():
    """Test PTR hostname synthesis for /56 network."""
    addr = ipaddress.IPv6Address("2001:db8:100:1234:5678:9abc:def0:1234")
    network = ipaddress.IPv6Network("2001:db8:100::/56")
    template = "host-%DIGITS%.example.com"
    
    config = NetworkConfig(network, template)
    hostname = synthesize_ptr_hostname(addr, config)
    
    assert hostname == "host-12345678abcdef01234.example.com"


def test_synthesize_ptr_hostname_80():
    """Test PTR hostname synthesis for /80 network."""
    addr = ipaddress.IPv6Address("2001:db8::1234:5678")
    network = ipaddress.IPv6Network("2001:db8::/80")
    template = "device-%DIGITS%.local"
    
    config = NetworkConfig(network, template)
    hostname = synthesize_ptr_hostname(addr, config)
    
    assert hostname == "device-12345678.local"


def test_find_matching_network():
    """Test finding matching network for address."""
    networks = [
        NetworkConfig(ipaddress.IPv6Network("2001:db8::/64"), "host-%DIGITS%.net"),
        NetworkConfig(ipaddress.IPv6Network("2001:4d88:100e:ccc0::/64"), "ipv6-%DIGITS%.example.com"),
        NetworkConfig(ipaddress.IPv6Network("fe80::/64"), "link-%DIGITS%.local"),
    ]
    
    # Test matching address
    addr = ipaddress.IPv6Address("2001:4d88:100e:ccc0::1")
    config = find_matching_network(addr, networks)
    assert config is not None
    assert config.template == "ipv6-%DIGITS%.example.com"
    
    # Test non-matching address
    addr = ipaddress.IPv6Address("2001:db9::1")
    config = find_matching_network(addr, networks)
    assert config is None


def test_find_matching_network_first_match():
    """Test that first matching network is returned."""
    networks = [
        NetworkConfig(ipaddress.IPv6Network("2001:db8::/32"), "broad-%DIGITS%.net"),
        NetworkConfig(ipaddress.IPv6Network("2001:db8::/64"), "specific-%DIGITS%.net"),
    ]
    
    addr = ipaddress.IPv6Address("2001:db8::1")
    config = find_matching_network(addr, networks)
    assert config is not None
    assert config.template == "broad-%DIGITS%.net"