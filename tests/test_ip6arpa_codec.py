"""Tests for IPv6 reverse DNS utilities."""

import ipaddress
import pytest

from dns_is_reverse.reverse import (
    ipv6_to_nibbles, nibbles_to_ipv6, ptr_qname_to_ipv6, ipv6_to_ptr_qname,
    extract_host_digits, digits_to_ipv6
)


def test_ipv6_to_nibbles():
    """Test IPv6 to nibbles conversion."""
    addr = ipaddress.IPv6Address("2001:4d88:100e:ccc0:216:eaff:fecb:826")
    nibbles = ipv6_to_nibbles(addr)
    assert nibbles == "20014d88100eccc00216eafffecb0826"


def test_nibbles_to_ipv6():
    """Test nibbles to IPv6 conversion."""
    nibbles = "20014d88100eccc00216eafffecb0826"
    addr = nibbles_to_ipv6(nibbles)
    assert addr == ipaddress.IPv6Address("2001:4d88:100e:ccc0:216:eaff:fecb:826")


def test_ptr_qname_to_ipv6():
    """Test PTR qname to IPv6 conversion."""
    qname = "6.2.8.0.b.c.e.f.f.f.a.e.6.1.2.0.0.c.c.c.e.0.0.1.8.8.d.4.1.0.0.2.ip6.arpa"
    addr = ptr_qname_to_ipv6(qname)
    assert addr == ipaddress.IPv6Address("2001:4d88:100e:ccc0:216:eaff:fecb:826")


def test_ptr_qname_to_ipv6_with_trailing_dot():
    """Test PTR qname with trailing dot."""
    qname = "6.2.8.0.b.c.e.f.f.f.a.e.6.1.2.0.0.c.c.c.e.0.0.1.8.8.d.4.1.0.0.2.ip6.arpa."
    addr = ptr_qname_to_ipv6(qname)
    assert addr == ipaddress.IPv6Address("2001:4d88:100e:ccc0:216:eaff:fecb:826")


def test_ptr_qname_invalid():
    """Test invalid PTR qname."""
    assert ptr_qname_to_ipv6("invalid.example.com") is None
    assert ptr_qname_to_ipv6("1.2.3.ip6.arpa") is None  # Too few nibbles


def test_ipv6_to_ptr_qname():
    """Test IPv6 to PTR qname conversion."""
    addr = ipaddress.IPv6Address("2001:4d88:100e:ccc0:216:eaff:fecb:826")
    qname = ipv6_to_ptr_qname(addr)
    expected = "6.2.8.0.b.c.e.f.f.f.a.e.6.1.2.0.0.c.c.c.e.0.0.1.8.8.d.4.1.0.0.2.ip6.arpa"
    assert qname == expected


def test_extract_host_digits_64():
    """Test extracting host digits from /64 network."""
    addr = ipaddress.IPv6Address("2001:4d88:100e:ccc0:216:eaff:fecb:826")
    network = ipaddress.IPv6Network("2001:4d88:100e:ccc0::/64")
    digits = extract_host_digits(addr, network)
    assert digits == "0216eafffecb0826"


def test_extract_host_digits_56():
    """Test extracting host digits from /56 network."""
    addr = ipaddress.IPv6Address("2001:db8:100:12:3456:789a:bcde:f012")
    network = ipaddress.IPv6Network("2001:db8:100::/56")
    digits = extract_host_digits(addr, network)
    assert digits == "123456789abcdef012"  # 72 bits = 18 hex chars


def test_extract_host_digits_out_of_network():
    """Test error when address not in network."""
    addr = ipaddress.IPv6Address("2001:db8::1")
    network = ipaddress.IPv6Network("2001:4d88::/64")
    
    with pytest.raises(ValueError, match="not in network"):
        extract_host_digits(addr, network)


def test_digits_to_ipv6_64():
    """Test converting digits to IPv6 in /64 network."""
    digits = "0216eafffecb0826"
    network = ipaddress.IPv6Network("2001:4d88:100e:ccc0::/64")
    addr = digits_to_ipv6(digits, network)
    assert addr == ipaddress.IPv6Address("2001:4d88:100e:ccc0:216:eaff:fecb:826")


def test_digits_to_ipv6_56():
    """Test converting digits to IPv6 in /56 network."""
    digits = "123456789abcdef012"
    network = ipaddress.IPv6Network("2001:db8:100::/56")
    addr = digits_to_ipv6(digits, network)
    assert addr == ipaddress.IPv6Address("2001:db8:100:12:3456:789a:bcde:f012")


def test_digits_to_ipv6_wrong_length():
    """Test error with wrong digits length."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    
    with pytest.raises(ValueError, match="Expected 16 digits"):
        digits_to_ipv6("123", network)


def test_digits_to_ipv6_invalid_hex():
    """Test error with invalid hex digits."""
    network = ipaddress.IPv6Network("2001:db8::/64")
    
    with pytest.raises(ValueError, match="Invalid hex digits"):
        digits_to_ipv6("gggggggggggggggg", network)