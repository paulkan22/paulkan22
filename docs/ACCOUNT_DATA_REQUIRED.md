# Какие данные нужны от Telegram-аккаунта

Ниже — полный список того, что нужно передать для корректного подключения аккаунта в систему.

## 1) Обязательные данные

### 1.1 Session файл
- Файл: `<account_name>.session`
- Назначение: авторизованный MTProto user session для Telethon

### 1.2 API credentials
- `api_id` (integer)
- `api_hash` (string)

### 1.3 Device/app fingerprint
- `device_model` (string)
- `system_version` (string)
- `app_version` (string)
- `lang_code` (string, например `ru`)
- `system_lang_code` (string, например `ru-RU`)

### 1.4 Proxy (SOCKS5)
- `scheme`: `socks5`
- `host`
- `port`
- `username` (optional)
- `password` (optional)

### 1.5 Internal routing
- `cluster_id` (integer)

---

## 2) Рекомендуемые (но опциональные) поля

- `lang_pack`
- `tz_offset`
- `account_label`
- `phone_hint` (маскированный номер, без хранения полного номера)

---

## 3) Пример JSON метаданных аккаунта

```json
{
  "api_id": 123456,
  "api_hash": "0123456789abcdef0123456789abcdef",
  "device_model": "Samsung SM-G998B",
  "system_version": "Android 14",
  "app_version": "10.13.2",
  "lang_code": "ru",
  "system_lang_code": "ru-RU",
  "lang_pack": "",
  "tz_offset": 10800,
  "proxy": {
    "scheme": "socks5",
    "host": "1.2.3.4",
    "port": 1080,
    "username": "proxy_user",
    "password": "proxy_pass"
  },
  "cluster_id": 2,
  "account_label": "acc_cluster2_01"
}
```

---

## 4) Что важно по безопасности

- Никогда не хранить эти JSON/session в публичных репозиториях.
- Прокси строго: 1 аккаунт = 1 прокси.
- Не стартовать все аккаунты одновременно после массовой загрузки.
- Вести журнал, кто и когда загружал аккаунты.
- Регулярно проверять валидность сессий и прокси.

---

## 5) Минимальный пакет для передачи в систему

На 1 аккаунт:
1. `*.session`
2. `*.json` (как выше)
3. `cluster_id`

Этого достаточно, чтобы начать подключение и безопасный прогрев лимитов.
