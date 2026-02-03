"""Tests for upstream fallback functionality."""

import socket
from unittest.mock import patch, MagicMock
import pytest

import dnslib
from dns_is_reverse.upstream import query_upstream


def test_query_upstream_success():
    """Test successful upstream query."""
    # Mock successful DNS response
    mock_response = dnslib.DNSRecord()
    mock_response.header.rcode = dnslib.RCODE.NOERROR
    mock_response.add_answer(dnslib.RR(
        rname="test.upstream",
        rtype=dnslib.QTYPE.PTR,
        rdata=dnslib.PTR("actual-host.example.com"),
        ttl=300
    ))
    
    with patch('socket.socket') as mock_socket_class:
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.recvfrom.return_value = (mock_response.pack(), ('8.8.8.8', 53))
        
        result = query_upstream('8.8.8.8', 'test.upstream')
        
        assert result == ['actual-host.example.com']
        mock_socket.sendto.assert_called_once()
        mock_socket.settimeout.assert_called_once_with(2.0)


def test_query_upstream_multiple_answers():
    """Test upstream query with multiple PTR answers."""
    mock_response = dnslib.DNSRecord()
    mock_response.header.rcode = dnslib.RCODE.NOERROR
    mock_response.add_answer(dnslib.RR(
        rname="test.upstream",
        rtype=dnslib.QTYPE.PTR,
        rdata=dnslib.PTR("host1.example.com"),
        ttl=300
    ))
    mock_response.add_answer(dnslib.RR(
        rname="test.upstream",
        rtype=dnslib.QTYPE.PTR,
        rdata=dnslib.PTR("host2.example.com"),
        ttl=300
    ))
    
    with patch('socket.socket') as mock_socket_class:
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.recvfrom.return_value = (mock_response.pack(), ('8.8.8.8', 53))
        
        result = query_upstream('8.8.8.8', 'test.upstream')
        
        assert result == ['host1.example.com', 'host2.example.com']


def test_query_upstream_nxdomain():
    """Test upstream query returning NXDOMAIN."""
    mock_response = dnslib.DNSRecord()
    mock_response.header.rcode = dnslib.RCODE.NXDOMAIN
    
    with patch('socket.socket') as mock_socket_class:
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.recvfrom.return_value = (mock_response.pack(), ('8.8.8.8', 53))
        
        result = query_upstream('8.8.8.8', 'test.upstream')
        
        assert result is None


def test_query_upstream_noerror_no_answers():
    """Test upstream query with NOERROR but no answers."""
    mock_response = dnslib.DNSRecord()
    mock_response.header.rcode = dnslib.RCODE.NOERROR
    # No answers added
    
    with patch('socket.socket') as mock_socket_class:
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.recvfrom.return_value = (mock_response.pack(), ('8.8.8.8', 53))
        
        result = query_upstream('8.8.8.8', 'test.upstream')
        
        assert result is None


def test_query_upstream_non_ptr_answers():
    """Test upstream query with non-PTR answers."""
    mock_response = dnslib.DNSRecord()
    mock_response.header.rcode = dnslib.RCODE.NOERROR
    mock_response.add_answer(dnslib.RR(
        rname="test.upstream",
        rtype=dnslib.QTYPE.A,  # Not PTR
        rdata=dnslib.A("192.168.1.1"),
        ttl=300
    ))
    
    with patch('socket.socket') as mock_socket_class:
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.recvfrom.return_value = (mock_response.pack(), ('8.8.8.8', 53))
        
        result = query_upstream('8.8.8.8', 'test.upstream')
        
        assert result is None


def test_query_upstream_timeout():
    """Test upstream query timeout."""
    with patch('socket.socket') as mock_socket_class:
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.recvfrom.side_effect = socket.timeout()
        
        result = query_upstream('8.8.8.8', 'test.upstream')
        
        assert result is None


def test_query_upstream_network_error():
    """Test upstream query network error."""
    with patch('socket.socket') as mock_socket_class:
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.sendto.side_effect = socket.error("Network unreachable")
        
        result = query_upstream('8.8.8.8', 'test.upstream')
        
        assert result is None


def test_query_upstream_ipv6():
    """Test upstream query to IPv6 address."""
    mock_response = dnslib.DNSRecord()
    mock_response.header.rcode = dnslib.RCODE.NOERROR
    mock_response.add_answer(dnslib.RR(
        rname="test.upstream",
        rtype=dnslib.QTYPE.PTR,
        rdata=dnslib.PTR("host.example.com"),
        ttl=300
    ))
    
    with patch('socket.socket') as mock_socket_class:
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.recvfrom.return_value = (mock_response.pack(), ('2001:4860:4860::8888', 53))
        
        result = query_upstream('2001:4860:4860::8888', 'test.upstream')
        
        assert result == ['host.example.com']
        # Verify IPv6 socket was created
        mock_socket_class.assert_called_with(socket.AF_INET6, socket.SOCK_DGRAM)


def test_query_upstream_custom_timeout():
    """Test upstream query with custom timeout."""
    mock_response = dnslib.DNSRecord()
    mock_response.header.rcode = dnslib.RCODE.NOERROR
    mock_response.add_answer(dnslib.RR(
        rname="test.upstream",
        rtype=dnslib.QTYPE.PTR,
        rdata=dnslib.PTR("host.example.com"),
        ttl=300
    ))
    
    with patch('socket.socket') as mock_socket_class:
        mock_socket = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.recvfrom.return_value = (mock_response.pack(), ('8.8.8.8', 53))
        
        result = query_upstream('8.8.8.8', 'test.upstream', timeout=5.0)
        
        assert result == ['host.example.com']
        mock_socket.settimeout.assert_called_once_with(5.0)