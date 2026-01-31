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
async def balance_topup_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Старт пополнения баланса (из баланса)."""
    await callback.answer()
    await state.clear()
    await state.set_state(BalanceFSM.choosing_amount)
    await callback.message.answer(BALANCE_TOPUP_COMING)
