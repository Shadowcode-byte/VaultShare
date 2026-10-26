"""simplify file_permissions to one grant per file-user pair

Revision ID: 1a0d3a870c76
Revises: 3cf8f7c1f7a2
Create Date: 2026-08-16 09:06:01.637662

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a0d3a870c76'
down_revision: Union[str, None] = '3cf8f7c1f7a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch_alter_table is required here because SQLite has no native
    # ALTER/DROP CONSTRAINT support -- Alembic works around that by
    # rebuilding the table under the hood. On Postgres this same code
    # just runs the two operations directly with no rebuild, so one
    # migration works correctly against both backends.
    with op.batch_alter_table("file_permissions") as batch_op:
        batch_op.drop_constraint("uq_file_user_permission", type_="unique")
        batch_op.create_unique_constraint("uq_file_user", ["file_id", "user_id"])


def downgrade() -> None:
    with op.batch_alter_table("file_permissions") as batch_op:
        batch_op.drop_constraint("uq_file_user", type_="unique")
        batch_op.create_unique_constraint("uq_file_user_permission", ["file_id", "user_id", "permission"])
