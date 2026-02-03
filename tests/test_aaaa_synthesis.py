"""Tests for AAAA record synthesis."""

import ipaddress
import pytest

from dns_is_reverse.config import NetworkConfig
from dns_is_reverse.synth import parse_aaaa_hostname, synthesize_aaaa_address, find_matching_template


def test_parse_aaaa_hostname():
    """Test parsing digits from AAAA hostname."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    template = "ipv6-%DIGITS%.example.com"
    config = NetworkConfig(network, template)
    
    # Valid hostname
    hostname = "ipv6-0216eafffecb0826.example.com"
    digits = parse_aaaa_hostname(hostname, config)
    assert digits == "0216eafffecb0826"
    
    # Case insensitive
    hostname = "ipv6-0216EAFFFECB0826.example.com"
    digits = parse_aaaa_hostname(hostname, config)
    assert digits == "0216eafffecb0826"
    
    # Non-matching hostname
    hostname = "other-host.example.com"
    digits = parse_aaaa_hostname(hostname, config)
    assert digits is None


def test_parse_aaaa_hostname_complex_template():
    """Test parsing with complex template."""
    network = ipaddress.IPv6Network("2001:db8::/56")
    template = "server-%DIGITS%-prod.example.org"
    config = NetworkConfig(network, template)
    
    hostname = "server-123456789abcdef012-prod.example.org"
    digits = parse_aaaa_hostname(hostname, config)
    assert digits == "123456789abcdef012"


def test_synthesize_aaaa_address():
    """Test AAAA address synthesis."""
    network = ipaddress.IPv6Network("2001:4d88:100e:ccc0::/64")
    template = "ipv6-%DIGITS%.example.com"
    config = NetworkConfig(network, template)
    
    hostname = "ipv6-0216eafffecb0826.example.com"
    addr = synthesize_aaaa_address(hostname, config)
    
    expected = ipaddress.IPv6Address("2001:4d88:100e:ccc0:216:eaff:fecb:826")
    assert addr == expected


def test_synthesize_aaaa_address_non_matching():
    """Test AAAA synthesis with non-matching hostname."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    template = "host-%DIGITS%.net"
    config = NetworkConfig(network, template)
    
    hostname = "other.example.com"
    addr = synthesize_aaaa_address(hostname, config)
    assert addr is None


def test_synthesize_aaaa_address_invalid_digits():
    """Test AAAA synthesis with invalid digits."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    template = "host-%DIGITS%.net"
    config = NetworkConfig(network, template)
    
    # Wrong length
    hostname = "host-123.net"
    addr = synthesize_aaaa_address(hostname, config)
    assert addr is None
    
    # Invalid hex
    hostname = "host-gggggggggggggggg.net"
    addr = synthesize_aaaa_address(hostname, config)
    assert addr is None


def test_find_matching_template():
    """Test finding template that matches hostname."""
    networks = [
        NetworkConfig(ipaddress.IPv6Network("2001:db8::/64"), "host-%DIGITS%.net"),
        NetworkConfig(ipaddress.IPv6Network("2001:4d88::/64"), "ipv6-%DIGITS%.example.com"),
        NetworkConfig(ipaddress.IPv6Network("fe80::/64"), "link-%DIGITS%.local"),
    ]
    
    # Test matching hostname
    hostname = "ipv6-0216eafffecb0826.example.com"
    config = find_matching_template(hostname, networks)
    assert config is not None
    assert config.template == "ipv6-%DIGITS%.example.com"
    
    # Test non-matching hostname
    hostname = "other.example.org"
    config = find_matching_template(hostname, networks)
    assert config is None


def test_find_matching_template_first_match():
    """Test that first matching template is returned."""
    networks = [
        NetworkConfig(ipaddress.IPv6Network("2001:db8::/64"), "host-%DIGITS%.net"),
        NetworkConfig(ipaddress.IPv6Network("2001:4d88::/64"), "host-%DIGITS%.net"),  # Same template
    ]
    
    hostname = "host-1234567890abcdef.net"
    config = find_matching_template(hostname, networks)
    assert config is not None
    assert config.network == ipaddress.IPv6Network("2001:db8::/64")


def test_synthesize_different_prefix_sizes():
    """Test AAAA synthesis for different prefix sizes."""
    # /56 network (18 hex digits)
    network56 = ipaddress.IPv6Network("2001:db8:100::/56")
    config56 = NetworkConfig(network56, "host-%DIGITS%.net")
    
    hostname = "host-123456789abcdef012.net"
    addr = synthesize_aaaa_address(hostname, config56)
    expected = ipaddress.IPv6Address("2001:db8:100:1234:5678:9abc:def0:12")
    assert addr == expected
    
    # /80 network (12 hex digits)
    network80 = ipaddress.IPv6Network("2001:db8::/80")
    config80 = NetworkConfig(network80, "device-%DIGITS%.local")
    
    hostname = "device-123456789abc.local"
    addr = synthesize_aaaa_address(hostname, config80)
    expected = ipaddress.IPv6Address("2001:db8::1234:5678:9abc")
    assert addr == expected