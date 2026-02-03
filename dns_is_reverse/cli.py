"""Command-line interface for DNS-is-reverse."""

import argparse
import sys
from pathlib import Path

from .dns_server import DNSServer
from .parser import parse_config


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DNS-is-reverse - IPv6 reverse DNS synthesizer")
    parser.add_argument(
        "--configfile",
        default="/etc/dns-is-reverse.conf",
        help="Configuration file path (default: /etc/dns-is-reverse.conf)"
    )
    parser.add_argument(
        "--listen",
        action="append",
        help="Additional listen address (can be used multiple times)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=53,
        help="Listen port (default: 53)"
    )
    parser.add_argument(
        "--querylog",
        action="store_true",
        help="Enable query logging to stdout"
    )
    
    args = parser.parse_args()
    
    # Read config file
    config_path = Path(args.configfile)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        config_text = config_path.read_text()
        config = parse_config(config_text)
    except Exception as e:
        print(f"Error parsing config: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Override config with CLI args
    if args.listen:
        config.listen_addresses.extend(args.listen)
    config.port = args.port
    config.query_log = args.querylog
    
    # Start server
    server = DNSServer(config)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()