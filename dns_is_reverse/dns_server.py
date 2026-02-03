"""DNS server implementation."""

import socket
import threading
from typing import Optional

import dnslib  # type: ignore

from .config import Config
from .reverse import ptr_qname_to_ipv6
from .synth import find_matching_network, find_matching_template, synthesize_ptr_hostname, synthesize_aaaa_address
from .upstream import query_upstream


class DNSServer:
    """UDP DNS server."""
    
    def __init__(self, config: Config):
        self.config = config
        self.running = False
        
    def handle_request(self, data: bytes, addr: tuple[str, int]) -> bytes:
        """Handle a single DNS request."""
        try:
            request = dnslib.DNSRecord.parse(data)
        except Exception:
            # Malformed request
            response = dnslib.DNSRecord()
            response.header.rcode = dnslib.RCODE.FORMERR
            return response.pack()  # type: ignore
        
        if self.config.query_log:
            print(f"Query from {addr[0]}: {request.q.qname} {dnslib.QTYPE[request.q.qtype]}")
        
        response = dnslib.DNSRecord()
        response.header.id = request.header.id
        response.header.qr = 1  # Response
        response.header.aa = 1  # Authoritative
        response.header.rcode = dnslib.RCODE.NOERROR  # Default to success
        response.add_question(request.q)
        
        qname = str(request.q.qname).rstrip('.')
        qtype = request.q.qtype
        
        if qtype == dnslib.QTYPE.PTR:
            self._handle_ptr(qname, response)
        elif qtype == dnslib.QTYPE.AAAA:
            self._handle_aaaa(qname, response)
        else:
            response.header.rcode = dnslib.RCODE.NXDOMAIN
            
        return response.pack()  # type: ignore
    
    def _handle_ptr(self, qname: str, response: dnslib.DNSRecord) -> None:
        """Handle PTR query."""
        # Convert PTR qname to IPv6
        addr = ptr_qname_to_ipv6(qname)
        if addr is None:
            response.header.rcode = dnslib.RCODE.NXDOMAIN
            return
        
        # Find matching network
        network_config = find_matching_network(addr, self.config.networks)
        if network_config is None:
            response.header.rcode = dnslib.RCODE.NXDOMAIN
            return
        
        # Try upstream first if configured
        if network_config.upstream:
            upstream_qname = f"{qname}.upstream"
            ptr_values = query_upstream(network_config.upstream, upstream_qname)
            if ptr_values:
                for ptr_value in ptr_values:
                    # Strip trailing dot from upstream response
                    ptr_value = ptr_value.rstrip('.')
                    rr = dnslib.RR(
                        rname=qname,
                        rtype=dnslib.QTYPE.PTR,
                        rdata=dnslib.PTR(ptr_value),
                        ttl=60
                    )
                    response.add_answer(rr)
                return
        
        # Synthesize locally
        hostname = synthesize_ptr_hostname(addr, network_config)
        rr = dnslib.RR(
            rname=qname,
            rtype=dnslib.QTYPE.PTR,
            rdata=dnslib.PTR(hostname),
            ttl=60
        )
        response.add_answer(rr)
    
    def _handle_aaaa(self, qname: str, response: dnslib.DNSRecord) -> None:
        """Handle AAAA query."""
        # Find matching template
        network_config = find_matching_template(qname, self.config.networks)
        if network_config is None:
            response.header.rcode = dnslib.RCODE.NXDOMAIN
            return
        
        # Synthesize address
        addr = synthesize_aaaa_address(qname, network_config)
        if addr is None:
            response.header.rcode = dnslib.RCODE.NXDOMAIN
            return
        
        rr = dnslib.RR(
            rname=qname,
            rtype=dnslib.QTYPE.AAAA,
            rdata=dnslib.AAAA(str(addr)),
            ttl=60
        )
        response.add_answer(rr)
    
    def start(self) -> None:
        """Start the DNS server."""
        self.running = True
        threads = []
        
        for listen_addr in self.config.listen_addresses:
            thread = threading.Thread(target=self._serve_address, args=(listen_addr,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            self.running = False
    
    def _serve_address(self, listen_addr: str) -> None:
        """Serve DNS requests on a single address."""
        family = socket.AF_INET6 if ':' in listen_addr else socket.AF_INET
        sock = socket.socket(family, socket.SOCK_DGRAM)
        
        try:
            sock.bind((listen_addr, self.config.port))
            print(f"Listening on {listen_addr}:{self.config.port}")
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(4096)
                    response_data = self.handle_request(data, addr)
                    sock.sendto(response_data, addr)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Error handling request: {e}")
        finally:
            sock.close()