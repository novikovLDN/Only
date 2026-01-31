"""
Payment handlers — подписка, пополнение баланса.

FSM flow, domain services для бизнес-логики.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.fsm.states import BalanceFSM, SubscriptionFSM
from app.texts import BALANCE_TOPUP_COMING

router = Router(name="payments")


# --- Subscription FSM (skeleton) ---

# --- Balance FSM (skeleton) ---

@router.callback_query(F.data == "balance_topup")
async def balance_topup_start(callback: CallbackQuery, user, state: FSMContext) -> None:
    """Старт пополнения баланса (из баланса)."""
    await callback.answer()
    await state.clear()
    await state.set_state(BalanceFSM.choosing_amount)
    from app.utils.message_lifecycle import send_screen_from_event
    await send_screen_from_event(callback, user.id, BALANCE_TOPUP_COMING)
