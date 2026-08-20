"""
NETWORK SECURITY & SSRF PROTECTION — core/network_security.py
Centralized validation and safe HTTP fetching for user/model-controlled URLs.
Protects against SSRF, DNS-rebinding, scheme smuggling, private IP access, and redirect bypasses.
"""

from __future__ import annotations

import ipaddress
import socket
import urllib.parse
from typing import Tuple, Dict, Any, Optional
import httpx


ALLOWED_SCHEMES: set[str] = {"http", "https"}
DEFAULT_MAX_REDIRECTS = 3
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB


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


def safe_fetch_url(
    url: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
    headers: Optional[Dict[str, str]] = None,
    allow_localhost: bool = False,
) -> Tuple[bool, str, int]:
    """
    Safely fetch an external HTTP/HTTPS resource with strict SSRF & redirect protection.

    Features:
      1. Pre-fetch URL validation (rejects private IPs, loopback, file/ftp schemes, credentials).
      2. Step-by-step redirect validation: every redirect target is independently verified
         before following to prevent redirect-based SSRF into private networks.
      3. Bounded streaming read up to max_bytes to prevent decompression/response bombs.
      4. Hard timeout enforcement.

    Returns
    -------
    (success, content_or_error, status_code)
    """
    current_url = url
    redirect_count = 0
    client_headers = headers.copy() if headers else {}
    client_headers.setdefault("User-Agent", "Sherly-Assistant/2.0")

    while redirect_count <= max_redirects:
        is_safe, reason = is_safe_url(current_url, allow_localhost=allow_localhost)
        if not is_safe:
            return False, f"SSRF Blocked: {reason}", 403

        try:
            with httpx.Client(
                follow_redirects=False,
                timeout=timeout,
                headers=client_headers,
            ) as client:
                with client.stream("GET", current_url) as response:
                    # Handle redirects manually to re-verify destination safety
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            return False, "Redirect response missing Location header", response.status_code

                        # Resolve relative URLs
                        current_url = urllib.parse.urljoin(current_url, location)
                        redirect_count += 1
                        continue

                    if response.status_code >= 400:
                        return False, f"HTTP Error {response.status_code}: {response.reason_phrase}", response.status_code

                    # Stream response up to max_bytes
                    chunks = []
                    total_bytes = 0
                    for chunk in response.iter_bytes(chunk_size=65536):
                        total_bytes += len(chunk)
                        if total_bytes > max_bytes:
                            return False, f"Response size exceeded limit of {max_bytes} bytes", 413
                        chunks.append(chunk)

                    raw_bytes = b"".join(chunks)
                    # Decode text safely
                    text = raw_bytes.decode(response.encoding or "utf-8", errors="replace")
                    return True, text, response.status_code

        except httpx.TimeoutException:
            return False, f"Request timed out after {timeout}s", 408
        except httpx.RequestError as exc:
            return False, f"Network request error: {exc}", 502
        except Exception as exc:
            return False, f"Unexpected fetch error: {exc}", 500

    return False, f"Exceeded maximum redirects ({max_redirects})", 310
