"""Tests for configuration parsing."""

import pytest
from ipaddress import IPv6Network

from dns_is_reverse.parser import parse_config
from dns_is_reverse.config import Config, NetworkConfig


def test_basic_config():
    """Test basic configuration parsing."""
    config_text = """
listen ::1
listen 127.0.0.1

network 2001:4d88:100e:ccc0::/64
    resolves to ipv6-%DIGITS%.example.com
    with upstream 2001:4860:4860::8888
"""
    
    config = parse_config(config_text)
    
    assert len(config.listen_addresses) == 2
    assert "::1" in config.listen_addresses
    assert "127.0.0.1" in config.listen_addresses
    
    assert len(config.networks) == 1
    network = config.networks[0]
    assert network.network == IPv6Network("2001:4d88:100e:ccc0::/64")
    assert network.template == "ipv6-%DIGITS%.example.com"
    assert network.upstream == "2001:4860:4860::8888"


def test_multiple_networks():
    """Test multiple network configurations."""
    config_text = """
listen ::1

network 2001:db8::/64
    resolves to host-%DIGITS%.net

network 2001:db8:1::/56
    resolves to server-%DIGITS%.org
    with upstream 8.8.8.8
"""
    
    config = parse_config(config_text)
    
    assert len(config.networks) == 2
    
    net1 = config.networks[0]
    assert net1.network == IPv6Network("2001:db8::/64")
    assert net1.template == "host-%DIGITS%.net"
    assert net1.upstream is None
    
    net2 = config.networks[1]
    assert net2.network == IPv6Network("2001:db8:1::/56")
    assert net2.template == "server-%DIGITS%.org"
    assert net2.upstream == "8.8.8.8"


def test_invalid_template():
    """Test template validation."""
    config_text = """
listen ::1
network 2001:db8::/64
    resolves to invalid-template
"""
    
    with pytest.raises(ValueError, match="exactly one %DIGITS%"):
        parse_config(config_text)


def test_multiple_digits_in_template():
    """Test template with multiple %DIGITS%."""
    config_text = """
listen ::1
network 2001:db8::/64
    resolves to %DIGITS%-%DIGITS%.com
"""
    
    with pytest.raises(ValueError, match="exactly one %DIGITS%"):
        parse_config(config_text)


def test_missing_listen():
    """Test error when no listen addresses."""
    config_text = """
network 2001:db8::/64
    resolves to host-%DIGITS%.com
"""
    
    with pytest.raises(ValueError, match="No listen addresses"):
        parse_config(config_text)


def test_missing_resolves_to():
    """Test error when network missing resolves to."""
    config_text = """
listen ::1
network 2001:db8::/64
    with upstream 8.8.8.8
"""
    
    with pytest.raises(ValueError, match="missing 'resolves to'"):
        parse_config(config_text)


def test_comments_and_empty_lines():
    """Test handling of comments and empty lines."""
    config_text = """
# This is a comment
listen ::1

# Another comment
network 2001:db8::/64
    # Indented comment
    resolves to host-%DIGITS%.com
    # More comments
    with upstream 8.8.8.8

# Final comment
"""
    
    config = parse_config(config_text)
    assert len(config.listen_addresses) == 1
    assert len(config.networks) == 1