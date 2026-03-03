from dataclasses import dataclass


@dataclass(frozen=True)
class ProxyConfig:
    scheme: str
    host: str
    port: int
    username: str | None = None
    password: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> 'ProxyConfig':
        scheme = str(data.get('scheme', 'socks5')).lower()
        if scheme != 'socks5':
            raise ValueError('Only socks5 proxy scheme is supported')
        host = str(data['host'])
        port = int(data['port'])
        username = data.get('username')
        password = data.get('password')
        return cls(scheme=scheme, host=host, port=port, username=username, password=password)


@dataclass(frozen=True)
class AccountMetadata:
    api_id: int
    api_hash: str
    device_model: str
    system_version: str
    app_version: str
    lang_code: str
    system_lang_code: str
    proxy: ProxyConfig
    cluster_id: int
    lang_pack: str | None = None
    tz_offset: int | None = None
    account_label: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> 'AccountMetadata':
        api_hash = str(data['api_hash']).strip()
        if len(api_hash) < 16:
            raise ValueError('api_hash seems invalid')

        return cls(
            api_id=int(data['api_id']),
            api_hash=api_hash,
            device_model=str(data['device_model']),
            system_version=str(data['system_version']),
            app_version=str(data['app_version']),
            lang_code=str(data['lang_code']),
            system_lang_code=str(data['system_lang_code']),
            lang_pack=data.get('lang_pack'),
            tz_offset=int(data['tz_offset']) if data.get('tz_offset') is not None else None,
            proxy=ProxyConfig.from_dict(data['proxy']),
            cluster_id=int(data['cluster_id']),
            account_label=data.get('account_label'),
        )

    def proxy_as_url(self) -> str:
        auth = ''
        if self.proxy.username and self.proxy.password:
            auth = f'{self.proxy.username}:{self.proxy.password}@'
        return f'{self.proxy.scheme}://{auth}{self.proxy.host}:{self.proxy.port}'
