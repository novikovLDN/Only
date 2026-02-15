"""Seed 150 motivation phrases per language.

Revision ID: 007
Revises: 006
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from app.core.motivation_phrases import MOTIVATION_EN, MOTIVATION_RU

    conn = op.get_bind()
    for phrase in MOTIVATION_RU:
        conn.execute(text("INSERT INTO motivation_phrases (language, text, is_used) VALUES ('ru', :t, false)").bindparams(t=phrase))
    for phrase in MOTIVATION_EN:
        conn.execute(text("INSERT INTO motivation_phrases (language, text, is_used) VALUES ('en', :t, false)").bindparams(t=phrase))


def downgrade() -> None:
    op.execute(text("DELETE FROM motivation_phrases"))
