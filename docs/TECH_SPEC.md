# Техническая спецификация (Production Safe Mode)

## Назначение

Система предназначена для:
- сбора пользователей из monitor-групп;
- вычисления пересечений с reference-группами через mutual-чаты;
- ранжирования пользователей по числу reference-пересечений;
- еженедельного экспорта новых/обновлённых записей в XLSX;
- управления всем циклом через Telegram-бота.

## Ключевая логика

1. **Сбор пользователей**:
   - приоритет `username`, иначе `user_id`;
   - при отсутствии username в экспорт обязательно добавляется `source_chat`.
2. **Mutual engine**:
   - MTProto: `messages.getCommonChats`;
   - фильтрация только по reference-группам;
   - сохранение `mutual_reference_count`, `mutual_groups_list`, `last_mutual_check`.
3. **Ранжирование**:
   - 0: cold;
   - 1: warm;
   - 2-3: hot;
   - 4+: very hot;
   - `reference_density = mutual_reference_count / total_reference_groups`.
4. **Экспорт (weekly)**:
   - пользователи, впервые найденные за 7 дней, **или** с ростом mutual;
   - сортировка: `mutual_reference_count DESC`, `monitor_group_count DESC`;
   - не удалять пользователей из БД, только фильтрация на этапе экспорта.

## Балансировщик

- Без burst-запросов.
- На аккаунт: `dynamic_limit` (начально 80, min 40, max 150).
- Jitter: 30-60 сек между mutual-запросами.
- Flood handling:
  - `<10 мин`: limit ×0.7 и cooldown 10-30 мин;
  - `>1 час`: статус `SLEEP`, `sleep_until = now + flood_time`, `dynamic_limit /= 2`.
- Рост лимита: +20% после 3 дней без flood.

## Модель статусов аккаунта

- ACTIVE
- COOLDOWN
- SLEEP
- ERROR

## Кластеризация

- Reference-группы делятся на кластеры.
- Аккаунт обслуживает только свой кластер.
- Mutual-задачи шардируются по cluster_id.

## Безопасность

- whitelist для доступа к боту;
- логирование действий;
- ежедневный backup PostgreSQL;
- запрет одновременного старта всех аккаунтов.
