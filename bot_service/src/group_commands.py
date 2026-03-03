import re


_LINK_RE = re.compile(r'^(?:https?://)?t\.me/(.+)$', re.IGNORECASE)


def parse_add_group_command(text: str) -> tuple[str, str, int | None]:
    """Format: /add_group <reference|monitor> <link_or_id> [cluster_id]."""
    parts = text.strip().split()
    if len(parts) not in (3, 4):
        raise ValueError('Usage: /add_group <reference|monitor> <link_or_id> [cluster_id]')

    _, group_type, group_ref, *tail = parts
    group_type = group_type.lower()
    if group_type not in {'reference', 'monitor'}:
        raise ValueError('group_type must be reference or monitor')

    cluster_id = int(tail[0]) if tail else None
    return group_type, group_ref, cluster_id


def normalize_group_ref(group_ref: str) -> str:
    ref = group_ref.strip()
    if not ref:
        raise ValueError('group reference is empty')
    return ref


def parse_proxy_value(proxy_raw: str) -> str:
    """Input: ip:port:login:password (login/password may not contain ':')."""
    parts = proxy_raw.strip().split(':')
    if len(parts) != 4:
        raise ValueError('Proxy format: ip:port:login:password')

    host, port, login, password = parts
    if not host or not port or not login or not password:
        raise ValueError('Proxy format: ip:port:login:password')

    try:
        port_int = int(port)
    except ValueError as exc:
        raise ValueError('Proxy port must be integer') from exc
    if port_int <= 0:
        raise ValueError('Proxy port must be positive')

    return f'socks5://{login}:{password}@{host}:{port_int}'


def extract_chat_identifier(group_ref: str) -> str:
    """Returns identifier suitable for bot.get_chat: @username or numeric chat id string."""
    ref = normalize_group_ref(group_ref)

    if ref.startswith('-100') or (ref.startswith('-') and ref[1:].isdigit()):
        return ref

    m = _LINK_RE.match(ref)
    if m:
        tail = m.group(1)
        if tail.startswith('c/'):
            parts = tail.split('/')
            if len(parts) >= 2 and parts[1].isdigit():
                return f"-100{parts[1]}"
        username = tail.split('/')[0]
        if username.startswith('+'):
            raise ValueError('Invite links are not supported for direct add_group, use numeric id or @username')
        return f'@{username.lstrip("@")}'

    if ref.startswith('@'):
        return ref

    if ref.isdigit():
        return f'-100{ref}'

    raise ValueError('Unsupported group reference. Use @username, t.me link, or numeric chat id')
