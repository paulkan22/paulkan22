from pathlib import Path

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message

from .admin_commands import parse_set_limit_command, parse_sleep_command
from .group_commands import extract_chat_identifier, parse_add_group_command, parse_proxy_value
from .keyboards import export_menu, main_menu
from .services import BotDataService
from .state import SystemStateStore
from .upload_flow import UploadState, load_metadata_json, sanitize_filename


def build_router(service: BotDataService, system_state: SystemStateStore) -> Router:
    router = Router()
    uploads: dict[int, UploadState] = {}

    @router.message(F.text == '/start')
    async def start(message: Message) -> None:
        await message.answer('Панель управления системой', reply_markup=main_menu())

    @router.message(F.text == '/upload_account')
    async def upload_account(message: Message) -> None:
        if not message.from_user:
            return
        uploads[message.from_user.id] = UploadState()
        await message.answer(
            'Отправьте 2 файла: *.session и *.json (metadata). Можно в любом порядке.\n'
            'После получения обоих файлов аккаунт будет зарегистрирован автоматически.'
        )

    @router.message(F.document)
    async def handle_document(message: Message) -> None:
        if not message.from_user or not message.document:
            return
        user_id = message.from_user.id
        state = uploads.get(user_id)
        if state is None:
            await message.answer('Сначала отправьте команду /upload_account')
            return

        accounts_dir = Path('data/accounts')
        incoming_dir = accounts_dir / 'incoming'
        incoming_dir.mkdir(parents=True, exist_ok=True)

        filename = sanitize_filename(message.document.file_name or 'file.bin')
        target = incoming_dir / filename
        await message.bot.download(message.document, destination=target)

        lower = filename.lower()
        if lower.endswith('.session'):
            state.session_path = target
            await message.answer(f'Получен session: {filename}')
        elif lower.endswith('.json'):
            state.metadata_path = target
            await message.answer(f'Получен metadata json: {filename}')
        else:
            await message.answer('Поддерживаются только .session и .json файлы')
            return

        if not state.ready():
            return

        try:
            metadata = load_metadata_json(state.metadata_path)
            await service.register_account_package(str(state.session_path), metadata)
            await service.log_action(user_id, 'register_account_package', '{"session":"%s"}' % str(state.session_path))
            uploads.pop(user_id, None)
            await message.answer('Аккаунт успешно зарегистрирован.')
        except Exception as exc:
            await message.answer(f'Ошибка регистрации аккаунта: {exc}')


    @router.message(F.text.startswith('/mark_backup'))
    async def mark_backup(message: Message) -> None:
        note = (message.text or '').replace('/mark_backup', '').strip() or None
        await service.mark_backup_run('ok', note)
        if message.from_user:
            await service.log_action(message.from_user.id, 'mark_backup', '{"note":"%s"}' % (note or ''))
        await message.answer('Backup run marked in DB.')


    @router.message(F.text.startswith('/set_proxy'))
    async def set_proxy(message: Message) -> None:
        try:
            parts = (message.text or '').split(maxsplit=2)
            if len(parts) != 3:
                raise ValueError('Usage: /set_proxy <account_id> <ip:port:login:password>')
            _, account_id_raw, proxy_raw = parts
            account_id = int(account_id_raw)
            proxy_url = parse_proxy_value(proxy_raw)
            await service.set_account_proxy(account_id, proxy_url)
            if message.from_user:
                await service.log_action(message.from_user.id, 'set_proxy', '{"account_id":%d}' % account_id)
            await message.answer(f'Прокси для аккаунта #{account_id} обновлён.')
        except Exception as exc:
            await message.answer(str(exc))

    @router.message(F.text.startswith('/add_group'))
    async def add_group(message: Message) -> None:
        try:
            group_type, group_ref, cluster_id = parse_add_group_command(message.text or '')
            chat_identifier = extract_chat_identifier(group_ref)
            chat = await message.bot.get_chat(chat_identifier)
            group_id = int(chat.id)
            title = chat.title or chat.username or str(group_id)
            await service.upsert_group(group_id, title, group_type, cluster_id)
            if message.from_user:
                await service.log_action(
                    message.from_user.id,
                    'add_group',
                    '{"group_id":%d,"type":"%s"}' % (group_id, group_type),
                )
            await message.answer(f'Группа добавлена/обновлена: {title} ({group_type}) id={group_id}')
        except Exception as exc:
            await message.answer(f'Ошибка add_group: {exc}')

    @router.message(F.text.startswith('/set_limit'))
    async def set_limit(message: Message) -> None:
        try:
            account_id, new_limit = parse_set_limit_command(message.text or '')
            await service.set_account_limit(account_id, new_limit)
            if message.from_user:
                await service.log_action(message.from_user.id, 'set_limit', '{"account_id":%d,"limit":%d}' % (account_id, new_limit))
            await message.answer(f'Лимит аккаунта #{account_id} установлен: {new_limit}')
        except Exception as exc:
            await message.answer(str(exc))

    @router.message(F.text.startswith('/sleep_account'))
    async def sleep_account(message: Message) -> None:
        try:
            account_id, minutes = parse_sleep_command(message.text or '')
            await service.set_account_sleep(account_id, minutes)
            if message.from_user:
                await service.log_action(message.from_user.id, 'sleep_account', '{"account_id":%d,"minutes":%d}' % (account_id, minutes))
            await message.answer(f'Аккаунт #{account_id} отправлен в SLEEP на {minutes} мин')
        except Exception as exc:
            await message.answer(str(exc))

    @router.callback_query(F.data == 'main')
    async def back_main(callback: CallbackQuery) -> None:
        await callback.message.edit_text('Панель управления системой', reply_markup=main_menu())
        await callback.answer()

    @router.callback_query(F.data == 'stats')
    async def stats(callback: CallbackQuery) -> None:
        data = await service.stats()
        running = await system_state.is_running()
        text = (
            f"Система: {'RUNNING' if running else 'STOPPED'}\n"
            f"Пользователи: {data['users']}\n"
            f"Группы (всего/reference/monitor): {data['groups_total']}/{data['groups_reference']}/{data['groups_monitor']}\n"
            f"Аккаунты: {data['accounts']}\n"
            f"Mutual tasks queued: {data['tasks_queued']}"
        )
        await callback.message.edit_text(text, reply_markup=main_menu())
        await callback.answer()

    @router.callback_query(F.data == 'accounts')
    async def accounts(callback: CallbackQuery) -> None:
        rows = await service.account_statuses()
        if not rows:
            text = 'Аккаунты не загружены.'
        else:
            text = '\n'.join(
                f"#{r['id']} {r['status']} | limit={r['dynamic_limit']} trust={r['trust_score']} cluster={r['cluster_id']}"
                for r in rows
            )
        text += '\n\nКоманды: /set_limit <account_id> <40..150>, /sleep_account <account_id> <minutes>, /set_proxy <account_id> <ip:port:login:password>, /add_group <reference|monitor> <link_or_id> [cluster_id], /upload_account'
        await callback.message.edit_text(text, reply_markup=main_menu())
        await callback.answer()

    @router.callback_query(F.data == 'groups')
    async def groups(callback: CallbackQuery) -> None:
        rows = await service.groups()
        if not rows:
            text = 'Список групп пуст.'
        else:
            text = '\n'.join(
                f"{r['type']} | {r['title'] or '-'} | {r['group_id']} | cluster={r['cluster_id']} | {r['status'] or '-'}"
                for r in rows[:20]
            )
        await callback.message.edit_text(text, reply_markup=main_menu())
        await callback.answer()

    @router.callback_query(F.data == 'export_menu')
    async def export_root(callback: CallbackQuery) -> None:
        await callback.message.edit_text('Выберите формат экспорта', reply_markup=export_menu())
        await callback.answer()

    @router.callback_query(F.data == 'export_7')
    async def export_7(callback: CallbackQuery) -> None:
        path = await service.export_weekly(Path('data/exports'))
        await callback.message.answer_document(FSInputFile(path))
        await callback.answer('Экспорт за 7 дней готов')

    @router.callback_query(F.data == 'export_30')
    async def export_30(callback: CallbackQuery) -> None:
        path = await service.export_by_days(Path('data/exports'), 30)
        await callback.message.answer_document(FSInputFile(path))
        await callback.answer('Экспорт за 30 дней готов')

    @router.callback_query(F.data == 'export_hot')
    async def export_hot(callback: CallbackQuery) -> None:
        path = await service.export_hot(Path('data/exports'), 30)
        await callback.message.answer_document(FSInputFile(path))
        await callback.answer('Экспорт hot-лидов готов')

    @router.callback_query(F.data == 'start_system')
    async def start_system(callback: CallbackQuery) -> None:
        await system_state.set_running(True)
        if callback.from_user:
            await service.log_action(callback.from_user.id, 'start_system')
        await callback.answer('Система переведена в RUNNING', show_alert=True)

    @router.callback_query(F.data == 'stop_system')
    async def stop_system(callback: CallbackQuery) -> None:
        await system_state.set_running(False)
        if callback.from_user:
            await service.log_action(callback.from_user.id, 'stop_system')
        await callback.answer('Система переведена в STOPPED', show_alert=True)

    @router.callback_query(F.data == 'balancer')
    async def balancer(callback: CallbackQuery) -> None:
        rows = await service.account_statuses()
        if not rows:
            text = 'Аккаунты не загружены.'
        else:
            text = '\n'.join(
                f"#{r['id']} {r['status']} | limit={r['dynamic_limit']} trust={r['trust_score']} sleep={r['sleep_until']}"
                for r in rows[:20]
            )
        text += '\n\nУправление: /set_limit <id> <40..150>, /sleep_account <id> <minutes>, /set_proxy <id> <ip:port:login:password>, /add_group <reference|monitor> <link_or_id> [cluster_id], /upload_account'
        await callback.message.edit_text(text, reply_markup=main_menu())
        await callback.answer()

    return router
