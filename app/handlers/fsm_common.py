"""
Общие handlers для FSM: /cancel, сброс при /start.

Защита от застревания: /cancel в любом state сбрасывает flow.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.texts import CANCELLED, ERROR_NOTHING_TO_CANCEL

router = Router(name="fsm_common")


@router.message(Command("cancel"))
@router.message(F.text == "/cancel")
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Сбросить FSM — пользователь отменил диалог."""
    current = await state.get_state()
    if current is None:
        await message.answer(ERROR_NOTHING_TO_CANCEL)
        return
    await state.clear()
    await message.answer(CANCELLED)


async def reset_fsm_if_stale(state: FSMContext, timeout_sec: int = 600) -> bool:
    """
    Проверить устарел ли FSM (по last_activity).
    Возвращает True если state сброшен.
    """
    from app.middlewares.fsm_middleware import FSM_LAST_ACTIVITY
    import time

    data = await state.get_data()
    last = data.get(FSM_LAST_ACTIVITY)
    if last is None:
        return False
    if time.time() - last > timeout_sec:
        await state.clear()
        return True
    return False
