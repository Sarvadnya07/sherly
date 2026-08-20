"""
NETWORK SECURITY & SSRF PROTECTION — core/network_security.py
Centralized validation for user-controlled URLs and outbound network calls.
"""

from __future__ import annotations

import ipaddress
import socket
import urllib.parse
from typing import Tuple


ALLOWED_SCHEMES: set[str] = {"http", "https"}


def is_safe_url(url: str, allow_localhost: bool = False) -> Tuple[bool, str]:
    """
    Validate that a given URL is safe to fetch and not attempting SSRF.

    Rejects:
      - Non-http/https schemes (file, gopher, ftp, data, javascript, etc.)
      - Embedded credentials (user:pass@host)
      - Loopback, private, link-local, multicast, reserved, and unspecified IP addresses
      - DNS rebinding / non-resolvable hosts

    Returns
    -------
    (bool, str): (is_safe, error_or_reason)
    """
    if not url or not isinstance(url, str):
        return False, "Empty or invalid URL."

    try:
        parsed = urllib.parse.urlparse(url.strip())
    except Exception as exc:
        return False, f"URL parse error: {exc}"

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return False, f"Disallowed URL scheme: '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

    if parsed.username or parsed.password:
        return False, "Embedded credentials in URL are not permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname in URL."

    # Check for direct IP address literal
    try:
        ip = ipaddress.ip_address(hostname)
        if not allow_localhost and (ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified):
            return False, f"Access to private or local IP address '{ip}' is blocked."
        return True, "URL is safe."
    except ValueError:
        pass  # Hostname is a domain name, proceed to DNS resolution check

    # Resolve domain to check all associated IP addresses
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme.lower() == "https" else 80))
    except socket.gaierror as exc:
        return False, f"DNS resolution failed for '{hostname}': {exc}"
    except Exception as exc:
        return False, f"Network error during resolution for '{hostname}': {exc}"

    if not addr_info:
        return False, f"No IP addresses resolved for hostname '{hostname}'."

    for entry in addr_info:
        sockaddr = entry[4]
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
            if not allow_localhost and (ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified):
                return False, f"Resolved IP address '{ip}' for '{hostname}' is in a protected or private range."
        except ValueError:
            return False, f"Invalid resolved IP '{ip_str}'."

    return True, "URL is safe."
