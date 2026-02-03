"""Configuration data structures for dns-is-reverse."""

from dataclasses import dataclass
from ipaddress import IPv6Network
from typing import Optional


@dataclass
class NetworkConfig:
    """Configuration for a single network."""
    network: IPv6Network
    template: str
    upstream: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate template contains exactly one %DIGITS%."""
        if self.template.count('%DIGITS%') != 1:
            raise ValueError(f"Template must contain exactly one %DIGITS%, got: {self.template}")


@dataclass
class Config:
    """Main configuration."""
    listen_addresses: list[str]
    networks: list[NetworkConfig]
    port: int = 53
    query_log: bool = False