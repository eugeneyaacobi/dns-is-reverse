"""End-to-end tests for DNS request handling."""

import ipaddress
from unittest.mock import patch, MagicMock

import dnslib
import pytest

from dns_is_reverse.config import Config, NetworkConfig
from dns_is_reverse.dns_server import DNSServer


@pytest.fixture
def test_config():
    """Test configuration with multiple networks."""
    networks = [
        NetworkConfig(
            ipaddress.IPv6Network("2001:4d88:100e:ccc0::/64"),
            "ipv6-%DIGITS%.nutzer.raumzeitlabor.de",
            "2001:4860:4860::8888"
        ),
        NetworkConfig(
            ipaddress.IPv6Network("2001:db8::/64"),
            "host-%DIGITS%.example.com"
        ),
    ]
    return Config(["::1"], networks, query_log=True)


def test_ptr_query_synthesis(test_config):
    """Test PTR query synthesis without upstream."""
    server = DNSServer(test_config)
    
    # Create PTR query for 2001:db8::1234:5678:9abc:def0
    qname = "0.f.e.d.c.b.a.9.8.7.6.5.4.3.2.1.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa"
    request = dnslib.DNSRecord.question(qname, 'PTR')
    
    response_data = server.handle_request(request.pack(), ('::1', 12345))
    response = dnslib.DNSRecord.parse(response_data)
    
    assert response.header.rcode == dnslib.RCODE.NOERROR
    assert len(response.rr) == 1
    assert response.rr[0].rtype == dnslib.QTYPE.PTR
    assert str(response.rr[0].rdata) == "host-123456789abcdef0.example.com."


def test_ptr_query_with_upstream_success(test_config):
    """Test PTR query with successful upstream response."""
    server = DNSServer(test_config)
    
    # Create PTR query for address in first network (has upstream)
    qname = "6.2.8.0.b.c.e.f.f.f.a.e.6.1.2.0.0.c.c.c.e.0.0.1.8.8.d.4.1.0.0.2.ip6.arpa"
    request = dnslib.DNSRecord.question(qname, 'PTR')
    
    with patch('dns_is_reverse.dns_server.query_upstream') as mock_upstream:
        mock_upstream.return_value = ['actual-host.example.com']
        
        response_data = server.handle_request(request.pack(), ('::1', 12345))
        response = dnslib.DNSRecord.parse(response_data)
        
        assert response.header.rcode == dnslib.RCODE.NOERROR
        assert len(response.rr) == 1
        assert str(response.rr[0].rdata) == "actual-host.example.com."
        
        # Verify upstream was queried with .upstream suffix
        mock_upstream.assert_called_once_with(
            "2001:4860:4860::8888",
            f"{qname}.upstream"
        )


def test_ptr_query_with_upstream_fallback(test_config):
    """Test PTR query with upstream failure, fallback to synthesis."""
    server = DNSServer(test_config)
    
    qname = "6.2.8.0.b.c.e.f.f.f.a.e.6.1.2.0.0.c.c.c.e.0.0.1.8.8.d.4.1.0.0.2.ip6.arpa"
    request = dnslib.DNSRecord.question(qname, 'PTR')
    
    with patch('dns_is_reverse.dns_server.query_upstream') as mock_upstream:
        mock_upstream.return_value = None  # Upstream failed
        
        response_data = server.handle_request(request.pack(), ('::1', 12345))
        response = dnslib.DNSRecord.parse(response_data)
        
        assert response.header.rcode == dnslib.RCODE.NOERROR
        assert len(response.rr) == 1
        assert str(response.rr[0].rdata) == "ipv6-0216eafffecb0826.nutzer.raumzeitlabor.de."


def test_ptr_query_out_of_network(test_config):
    """Test PTR query for address not in any configured network."""
    server = DNSServer(test_config)
    
    # Query for 2001:db9::1 (not in any configured network)
    qname = "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.9.b.d.1.0.0.2.ip6.arpa"
    request = dnslib.DNSRecord.question(qname, 'PTR')
    
    response_data = server.handle_request(request.pack(), ('::1', 12345))
    response = dnslib.DNSRecord.parse(response_data)
    
    assert response.header.rcode == dnslib.RCODE.NXDOMAIN
    assert len(response.rr) == 0


def test_aaaa_query_synthesis(test_config):
    """Test AAAA query synthesis."""
    server = DNSServer(test_config)
    
    request = dnslib.DNSRecord.question("host-123456789abcdef0.example.com", 'AAAA')
    
    response_data = server.handle_request(request.pack(), ('::1', 12345))
    response = dnslib.DNSRecord.parse(response_data)
    
    assert response.header.rcode == dnslib.RCODE.NOERROR
    assert len(response.rr) == 1
    assert response.rr[0].rtype == dnslib.QTYPE.AAAA
    assert str(response.rr[0].rdata) == "2001:db8::1234:5678:9abc:def0"


def test_aaaa_query_no_template_match(test_config):
    """Test AAAA query for hostname that doesn't match any template."""
    server = DNSServer(test_config)
    
    request = dnslib.DNSRecord.question("other-host.example.org", 'AAAA')
    
    response_data = server.handle_request(request.pack(), ('::1', 12345))
    response = dnslib.DNSRecord.parse(response_data)
    
    assert response.header.rcode == dnslib.RCODE.NXDOMAIN
    assert len(response.rr) == 0


def test_aaaa_query_invalid_digits(test_config):
    """Test AAAA query with invalid hex digits."""
    server = DNSServer(test_config)
    
    request = dnslib.DNSRecord.question("host-gggggggggggggggg.example.com", 'AAAA')
    
    response_data = server.handle_request(request.pack(), ('::1', 12345))
    response = dnslib.DNSRecord.parse(response_data)
    
    assert response.header.rcode == dnslib.RCODE.NXDOMAIN
    assert len(response.rr) == 0


def test_unsupported_query_type(test_config):
    """Test unsupported query type returns NXDOMAIN."""
    server = DNSServer(test_config)
    
    request = dnslib.DNSRecord.question("example.com", 'A')
    
    response_data = server.handle_request(request.pack(), ('::1', 12345))
    response = dnslib.DNSRecord.parse(response_data)
    
    assert response.header.rcode == dnslib.RCODE.NXDOMAIN
    assert len(response.rr) == 0


def test_malformed_request(test_config):
    """Test malformed DNS request returns FORMERR."""
    server = DNSServer(test_config)
    
    malformed_data = b"invalid dns data"
    
    response_data = server.handle_request(malformed_data, ('::1', 12345))
    response = dnslib.DNSRecord.parse(response_data)
    
    assert response.header.rcode == dnslib.RCODE.FORMERR


def test_authoritative_flag(test_config):
    """Test that responses have authoritative flag set."""
    server = DNSServer(test_config)
    
    request = dnslib.DNSRecord.question("host-123456789abcdef0.example.com", 'AAAA')
    
    response_data = server.handle_request(request.pack(), ('::1', 12345))
    response = dnslib.DNSRecord.parse(response_data)
    
    assert response.header.aa == 1  # Authoritative answer


def test_query_logging(test_config, capsys):
    """Test query logging functionality."""
    server = DNSServer(test_config)
    
    request = dnslib.DNSRecord.question("host-123456789abcdef0.example.com", 'AAAA')
    
    server.handle_request(request.pack(), ('::1', 12345))
    
    captured = capsys.readouterr()
    assert "Query from ::1: host-123456789abcdef0.example.com. AAAA" in captured.out


def test_response_id_matches_request(test_config):
    """Test that response ID matches request ID."""
    server = DNSServer(test_config)
    
    request = dnslib.DNSRecord.question("host-123456789abcdef0.example.com", 'AAAA')
    request.header.id = 12345
    
    response_data = server.handle_request(request.pack(), ('::1', 12345))
    response = dnslib.DNSRecord.parse(response_data)
    
    assert response.header.id == 12345


def test_ttl_values(test_config):
    """Test that responses have consistent TTL values."""
    server = DNSServer(test_config)
    
    request = dnslib.DNSRecord.question("host-123456789abcdef0.example.com", 'AAAA')
    
    response_data = server.handle_request(request.pack(), ('::1', 12345))
    response = dnslib.DNSRecord.parse(response_data)
    
    assert response.rr[0].ttl == 60