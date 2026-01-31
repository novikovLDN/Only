"""
Aggregate router — регистрация всех handler-роутеров.
"""

from aiogram import Router

from app.handlers import start, habits, admin, fsm_common, payments, profile, achievements, errors

router = Router(name="main")
router.include_router(errors.router)  # Error handler first
router.include_router(fsm_common.router)  # /cancel
router.include_router(start.router)
router.include_router(profile.router)
router.include_router(achievements.router)
router.include_router(habits.router)
router.include_router(payments.router)
router.include_router(admin.router)
