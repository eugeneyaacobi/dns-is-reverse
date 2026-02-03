"""Tests for template matching functionality."""

import ipaddress
import pytest

from dns_is_reverse.config import NetworkConfig
from dns_is_reverse.synth import parse_aaaa_hostname


def test_template_exact_match():
    """Test exact template matching."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    template = "host-1234567890abcdef.example.com"
    config = NetworkConfig(network, template.replace("1234567890abcdef", "%DIGITS%"))
    
    digits = parse_aaaa_hostname("host-1234567890abcdef.example.com", config)
    assert digits == "1234567890abcdef"


def test_template_with_special_chars():
    """Test template with regex special characters."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    template = "host-%DIGITS%.example.com"
    config = NetworkConfig(network, template)
    
    # Should not match due to different domain
    digits = parse_aaaa_hostname("host-1234567890abcdef.example.org", config)
    assert digits is None
    
    # Should match exact template
    digits = parse_aaaa_hostname("host-1234567890abcdef.example.com", config)
    assert digits == "1234567890abcdef"


def test_template_with_dots_and_dashes():
    """Test template with dots and dashes that need escaping."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    template = "ipv6-%DIGITS%.sub-domain.example-site.com"
    config = NetworkConfig(network, template)
    
    hostname = "ipv6-fedcba9876543210.sub-domain.example-site.com"
    digits = parse_aaaa_hostname(hostname, config)
    assert digits == "fedcba9876543210"
    
    # Should not match partial
    digits = parse_aaaa_hostname("ipv6-fedcba9876543210.sub-domain.example-site.org", config)
    assert digits is None


def test_template_case_insensitive():
    """Test case insensitive template matching."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    template = "HOST-%DIGITS%.EXAMPLE.COM"
    config = NetworkConfig(network, template)
    
    # Lowercase hostname should match uppercase template
    digits = parse_aaaa_hostname("host-abcdef1234567890.example.com", config)
    assert digits == "abcdef1234567890"
    
    # Mixed case should work
    digits = parse_aaaa_hostname("Host-ABCDEF1234567890.Example.Com", config)
    assert digits == "abcdef1234567890"


def test_template_prefix_suffix():
    """Test template with both prefix and suffix."""
    network = ipaddress.IPv6Network("2001:db8::/56")  # 18 hex digits
    template = "prefix-%DIGITS%-suffix.domain.tld"
    config = NetworkConfig(network, template)
    
    hostname = "prefix-123456789abcdef012-suffix.domain.tld"
    digits = parse_aaaa_hostname(hostname, config)
    assert digits == "123456789abcdef012"
    
    # Missing prefix should not match
    digits = parse_aaaa_hostname("123456789abcdef012-suffix.domain.tld", config)
    assert digits is None
    
    # Missing suffix should not match
    digits = parse_aaaa_hostname("prefix-123456789abcdef012.domain.tld", config)
    assert digits is None


def test_template_digits_only():
    """Test template that is just %DIGITS%."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    template = "%DIGITS%"
    config = NetworkConfig(network, template)
    
    digits = parse_aaaa_hostname("1234567890abcdef", config)
    assert digits == "1234567890abcdef"
    
    # Should not match with extra characters
    digits = parse_aaaa_hostname("1234567890abcdef.com", config)
    assert digits is None


def test_template_multiple_subdomains():
    """Test template with multiple subdomain levels."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    template = "%DIGITS%.hosts.internal.example.com"
    config = NetworkConfig(network, template)
    
    hostname = "fedcba0987654321.hosts.internal.example.com"
    digits = parse_aaaa_hostname(hostname, config)
    assert digits == "fedcba0987654321"
    
    # Wrong subdomain should not match
    digits = parse_aaaa_hostname("fedcba0987654321.other.internal.example.com", config)
    assert digits is None


def test_template_validation_no_digits():
    """Test template validation fails without %DIGITS%."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    
    with pytest.raises(ValueError, match="exactly one %DIGITS%"):
        NetworkConfig(network, "host.example.com")


def test_template_validation_multiple_digits():
    """Test template validation fails with multiple %DIGITS%."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    
    with pytest.raises(ValueError, match="exactly one %DIGITS%"):
        NetworkConfig(network, "%DIGITS%-%DIGITS%.example.com")