"""add payment distribution tables (members, personal_accounts, payment_distributions)

Revision ID: 0013
Revises: 0012
Create Date: 2026-03-20

Phase 3: Payment Distribution - core tables for member accounts and payment allocation.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create members table
    op.create_table(
        "members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("cooperative_id", sa.Uuid(), nullable=False),
        sa.Column("personal_account_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, default="active"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["owners.id"], name="fk_members_owner_id"
        ),
        sa.ForeignKeyConstraint(
            ["cooperative_id"], ["cooperatives.id"], name="fk_members_cooperative_id"
        ),
        sa.ForeignKeyConstraint(
            ["personal_account_id"],
            ["personal_accounts.id"],
            name="fk_members_personal_account_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_id", "cooperative_id", name="uq_members_owner_cooperative"
        ),
        comment="Члены СТ (связь Owner ↔ Cooperative)",
    )
    op.create_index("ix_members_owner_id", "members", ["owner_id"])
    op.create_index("ix_members_cooperative_id", "members", ["cooperative_id"])

    # Create personal_accounts table
    op.create_table(
        "personal_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("cooperative_id", sa.Uuid(), nullable=False),
        sa.Column("account_number", sa.String(length=50), nullable=False),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False, default=0),
        sa.Column("status", sa.String(length=20), nullable=False, default="active"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["member_id"], ["members.id"], name="fk_personal_accounts_member_id"
        ),
        sa.ForeignKeyConstraint(
            ["cooperative_id"],
            ["cooperatives.id"],
            name="fk_personal_accounts_cooperative_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_number", name="uq_personal_accounts_number"),
        sa.CheckConstraint(
            "balance >= 0", name="ck_personal_accounts_balance_non_negative"
        ),
        comment="Лицевые счета членов СТ",
    )
    op.create_index("ix_personal_accounts_member_id", "personal_accounts", ["member_id"])
    op.create_index(
        "ix_personal_accounts_cooperative_id", "personal_accounts", ["cooperative_id"]
    )

    # Add foreign key from members.personal_account_id (deferred until after personal_accounts exists)
    # Already created above

    # Create personal_account_transactions table
    op.create_table(
        "personal_account_transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=True),
        sa.Column("distribution_id", sa.Uuid(), nullable=True),
        sa.Column("transaction_number", sa.String(length=50), nullable=False),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["personal_accounts.id"],
            name="fk_pa_transactions_account_id",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.id"], name="fk_pa_transactions_payment_id"
        ),
        sa.ForeignKeyConstraint(
            ["distribution_id"],
            ["payment_distributions.id"],
            name="fk_pa_transactions_distribution_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "transaction_number", name="uq_pa_transactions_number"
        ),
        sa.CheckConstraint(
            "amount >= 0", name="ck_pa_transactions_amount_non_negative"
        ),
        comment="Транзакции по лицевым счетам",
    )
    op.create_index(
        "ix_pa_transactions_account_id", "personal_account_transactions", ["account_id"]
    )
    op.create_index(
        "ix_pa_transactions_payment_id", "personal_account_transactions", ["payment_id"]
    )
    op.create_index(
        "ix_pa_transactions_distribution_id",
        "personal_account_transactions",
        ["distribution_id"],
    )

    # Create payment_distributions table
    op.create_table(
        "payment_distributions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=False),
        sa.Column("financial_subject_id", sa.Uuid(), nullable=False),
        sa.Column("accrual_id", sa.Uuid(), nullable=True),
        sa.Column("distribution_number", sa.String(length=50), nullable=False),
        sa.Column("distributed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, default="applied"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.id"], name="fk_payment_distributions_payment_id"
        ),
        sa.ForeignKeyConstraint(
            ["financial_subject_id"],
            ["financial_subjects.id"],
            name="fk_payment_distributions_subject_id",
        ),
        sa.ForeignKeyConstraint(
            ["accrual_id"], ["accruals.id"], name="fk_payment_distributions_accrual_id"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "distribution_number", name="uq_payment_distributions_number"
        ),
        sa.CheckConstraint(
            "amount >= 0", name="ck_payment_distributions_amount_non_negative"
        ),
        comment="Распределения платежей по начислениям",
    )
    op.create_index(
        "ix_payment_distributions_payment_id", "payment_distributions", ["payment_id"]
    )
    op.create_index(
        "ix_payment_distributions_subject_id",
        "payment_distributions",
        ["financial_subject_id"],
    )
    op.create_index(
        "ix_payment_distributions_accrual_id", "payment_distributions", ["accrual_id"]
    )


def downgrade() -> None:
    op.drop_table("payment_distributions")
    op.drop_table("personal_account_transactions")
    op.drop_table("personal_accounts")
    op.drop_table("members")
