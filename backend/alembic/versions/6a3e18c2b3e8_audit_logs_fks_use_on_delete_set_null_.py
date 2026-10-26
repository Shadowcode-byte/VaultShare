"""audit_logs FKs use ON DELETE SET NULL so deleting a file or user never blocks on its own audit trail

Revision ID: 6a3e18c2b3e8
Revises: d1c5f9a1fb8b
Create Date: 2026-09-03 08:01:12.864942

NOTE: hand-written, dialect-aware, and NOT a simple autogenerate output.
Two real tooling gaps surfaced writing this one:

1. SQLite never named these foreign keys in the first place (no
   CONSTRAINT name in the original CREATE TABLE), so there is nothing
   to `DROP CONSTRAINT <name>` — Alembic's batch mode still requires a
   name even for a table it's about to recreate from scratch. The only
   reliable fix on SQLite is a manual table-rebuild via raw SQL.
2. Postgres, by contrast, ALWAYS auto-names an unnamed foreign key
   using the pattern `<table>_<column>_fkey` — so the exact same
   migration needs a completely different code path per dialect, or it
   silently does nothing (or errors) on one of the two databases this
   project actually runs on.
"""
from typing import Sequence, Union

from alembic import op

revision: str = '6a3e18c2b3e8'
down_revision: Union[str, None] = 'd1c5f9a1fb8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute("PRAGMA foreign_keys=OFF")
        op.execute("""
            CREATE TABLE audit_logs_new (
                id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36),
                file_id VARCHAR(36),
                action VARCHAR(27) NOT NULL,
                result VARCHAR(7) NOT NULL,
                event_metadata JSON,
                timestamp DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(file_id) REFERENCES files (id) ON DELETE SET NULL,
                FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
            )
        """)
        op.execute("INSERT INTO audit_logs_new SELECT * FROM audit_logs")
        op.execute("DROP TABLE audit_logs")
        op.execute("ALTER TABLE audit_logs_new RENAME TO audit_logs")
        op.execute("CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id)")
        op.execute("CREATE INDEX ix_audit_logs_file_id ON audit_logs (file_id)")
        op.execute("CREATE INDEX ix_audit_logs_action ON audit_logs (action)")
        op.execute("CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp)")
        op.execute("PRAGMA foreign_keys=ON")
    else:
        op.drop_constraint("audit_logs_user_id_fkey", "audit_logs", type_="foreignkey")
        op.drop_constraint("audit_logs_file_id_fkey", "audit_logs", type_="foreignkey")
        op.create_foreign_key(
            "audit_logs_user_id_fkey", "audit_logs", "users", ["user_id"], ["id"], ondelete="SET NULL"
        )
        op.create_foreign_key(
            "audit_logs_file_id_fkey", "audit_logs", "files", ["file_id"], ["id"], ondelete="SET NULL"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute("PRAGMA foreign_keys=OFF")
        op.execute("""
            CREATE TABLE audit_logs_new (
                id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36),
                file_id VARCHAR(36),
                action VARCHAR(27) NOT NULL,
                result VARCHAR(7) NOT NULL,
                event_metadata JSON,
                timestamp DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(file_id) REFERENCES files (id),
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
        """)
        op.execute("INSERT INTO audit_logs_new SELECT * FROM audit_logs")
        op.execute("DROP TABLE audit_logs")
        op.execute("ALTER TABLE audit_logs_new RENAME TO audit_logs")
        op.execute("CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id)")
        op.execute("CREATE INDEX ix_audit_logs_file_id ON audit_logs (file_id)")
        op.execute("CREATE INDEX ix_audit_logs_action ON audit_logs (action)")
        op.execute("CREATE INDEX ix_audit_logs_timestamp ON audit_logs (timestamp)")
        op.execute("PRAGMA foreign_keys=ON")
    else:
        op.drop_constraint("audit_logs_user_id_fkey", "audit_logs", type_="foreignkey")
        op.drop_constraint("audit_logs_file_id_fkey", "audit_logs", type_="foreignkey")
        op.create_foreign_key("audit_logs_user_id_fkey", "audit_logs", "users", ["user_id"], ["id"])
        op.create_foreign_key("audit_logs_file_id_fkey", "audit_logs", "files", ["file_id"], ["id"])
