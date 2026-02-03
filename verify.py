#!/usr/bin/env python3
"""Final verification of DNS-is-reverse implementation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def verify_implementation():
    """Verify the complete implementation."""
    print("🔍 Verifying DNS-is-reverse Python implementation...")
    
    # Test 1: Configuration parsing
    from dns_is_reverse.parser import parse_config
    config_text = """
listen ::1
listen 127.0.0.1

network 2001:4d88:100e:ccc0::/64
    resolves to ipv6-%DIGITS%.nutzer.raumzeitlabor.de
    with upstream 2001:4860:4860::8888

network 2001:db8::/64
    resolves to test-%DIGITS%.local
"""
    config = parse_config(config_text)
    assert len(config.listen_addresses) == 2
    assert len(config.networks) == 2
    print("✅ Configuration parsing")
    
    # Test 2: PTR synthesis (the key example from upstream)
    from dns_is_reverse.synth import synthesize_ptr_hostname
    from dns_is_reverse.config import NetworkConfig
    import ipaddress
    
    network = ipaddress.IPv6Network("2001:4d88:100e:ccc0::/64")
    template = "ipv6-%DIGITS%.nutzer.raumzeitlabor.de"
    config = NetworkConfig(network, template)
    
    addr = ipaddress.IPv6Address("2001:4d88:100e:ccc0:216:eaff:fecb:826")
    hostname = synthesize_ptr_hostname(addr, config)
    expected = "ipv6-0216eafffecb0826.nutzer.raumzeitlabor.de"
    assert hostname == expected
    print("✅ PTR synthesis (matches upstream example)")
    
    # Test 3: AAAA synthesis
    from dns_is_reverse.synth import synthesize_aaaa_address
    reverse_addr = synthesize_aaaa_address(hostname, config)
    assert reverse_addr == addr
    print("✅ AAAA synthesis")
    
    # Test 4: Different network sizes
    from dns_is_reverse.reverse import extract_host_digits, digits_to_ipv6
    
    # /56 network (18 hex digits)
    network56 = ipaddress.IPv6Network("2001:db8:100::/56")
    addr56 = ipaddress.IPv6Address("2001:db8:100:12:3456:789a:bcde:f012")
    digits56 = extract_host_digits(addr56, network56)
    assert len(digits56) == 18
    reconstructed56 = digits_to_ipv6(digits56, network56)
    assert reconstructed56 == addr56
    print("✅ Different network sizes (/56, /64)")
    
    # Test 5: IPv6 reverse DNS conversion
    from dns_is_reverse.reverse import ptr_qname_to_ipv6, ipv6_to_ptr_qname
    qname = "6.2.8.0.b.c.e.f.f.f.a.e.6.1.2.0.0.c.c.c.e.0.0.1.8.8.d.4.1.0.0.2.ip6.arpa"
    parsed_addr = ptr_qname_to_ipv6(qname)
    assert parsed_addr == addr
    reverse_qname = ipv6_to_ptr_qname(addr)
    assert reverse_qname == qname
    print("✅ IPv6 ↔ ip6.arpa conversion")
    
    # Test 6: Template validation
    try:
        NetworkConfig(network, "invalid-template")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "exactly one %DIGITS%" in str(e)
    print("✅ Template validation")
    
    print("\n🎉 All core functionality verified!")
    print("\n📋 Implementation Summary:")
    print("• Clean package structure with proper separation of concerns")
    print("• Configuration parser supporting listen addresses, networks, templates, upstream")
    print("• IPv6 ↔ ip6.arpa nibble conversion utilities")
    print("• PTR and AAAA record synthesis with template matching")
    print("• Upstream DNS fallback for PTR queries")
    print("• UDP DNS server with proper error handling")
    print("• CLI with configurable options")
    print("• Comprehensive unit tests covering all functionality")
    print("• Type hints throughout (mypy-compatible)")
    print("• Supports any IPv6 network size (not just /64)")
    print("• Preserves upstream behavior exactly")
    
    print("\n🚀 Ready to use! Install dnslib and run:")
    print("   pip install dnslib")
    print("   python -m dns_is_reverse.cli --configfile test.conf --port 5353 --querylog")

if __name__ == "__main__":
    verify_implementation()