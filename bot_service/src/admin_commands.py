def parse_set_limit_command(text: str) -> tuple[int, int]:
    """Format: /set_limit <account_id> <limit>"""
    parts = text.strip().split()
    if len(parts) != 3:
        raise ValueError('Usage: /set_limit <account_id> <limit>')
    _, account_id, new_limit = parts
    return int(account_id), int(new_limit)


def parse_sleep_command(text: str) -> tuple[int, int]:
    """Format: /sleep_account <account_id> <minutes>"""
    parts = text.strip().split()
    if len(parts) != 3:
        raise ValueError('Usage: /sleep_account <account_id> <minutes>')
    _, account_id, minutes = parts
    return int(account_id), int(minutes)
