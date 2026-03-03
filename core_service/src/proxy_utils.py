from urllib.parse import urlparse


def parse_socks5_proxy(proxy_url: str | None):
    if not proxy_url:
        return None
    parsed = urlparse(proxy_url)
    if parsed.scheme != 'socks5' or not parsed.hostname or not parsed.port:
        return None
    if parsed.username and parsed.password:
        return ('socks5', parsed.hostname, parsed.port, True, parsed.username, parsed.password)
    return ('socks5', parsed.hostname, parsed.port)
