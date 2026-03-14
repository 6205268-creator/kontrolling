"""add payment distribution tables

Revision ID: 0e7532228d92
Revises: previous_revision
Create Date: 2026-03-14 10:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0e7532228d92"
down_revision = None  # TODO: Указать предыдущую миграцию
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Member
    op.create_table(
        "members",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", UUID(as_uuid=True), nullable=False),
        sa.Column("cooperative_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", String(50), nullable=False, default="active"),
        sa.Column("joined_date", DateTime, nullable=False),
        sa.Column("created_at", DateTime, nullable=False),
        sa.Column("updated_at", DateTime, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["owners.id"]),
        sa.ForeignKeyConstraint(["cooperative_id"], ["cooperatives.id"]),
    )
    op.create_index("ix_members_owner", "members", ["owner_id"])
    op.create_index("ix_members_cooperative", "members", ["cooperative_id"])
    op.create_index("ix_members_status", "members", ["status"])
    op.create_unique_constraint(
        "uq_members_owner_cooperative", "members", ["owner_id", "cooperative_id"]
    )

    # MemberPlot
    op.create_table(
        "member_plots",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", UUID(as_uuid=True), nullable=False),
        sa.Column("land_plot_id", UUID(as_uuid=True), nullable=False),
        sa.Column("share_numerator", Integer, nullable=False),
        sa.Column("share_denominator", Integer, nullable=False),
        sa.Column("is_primary", Boolean, nullable=False, default=False),
        sa.Column("created_at", DateTime, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"]),
        sa.ForeignKeyConstraint(["land_plot_id"], ["land_plots.id"]),
    )
    op.create_index("ix_member_plots_member", "member_plots", ["member_id"])
    op.create_index("ix_member_plots_land_plot", "member_plots", ["land_plot_id"])

    # PersonalAccount
    op.create_table(
        "personal_accounts",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", UUID(as_uuid=True), nullable=False),
        sa.Column("cooperative_id", UUID(as_uuid=True), nullable=False),
        sa.Column("account_number", String(50), nullable=False, unique=True),
        sa.Column("balance", Numeric(10, 2), nullable=False, default=0.00),
        sa.Column("status", String(50), nullable=False, default="active"),
        sa.Column("opened_at", DateTime, nullable=False),
        sa.Column("closed_at", DateTime, nullable=True),
        sa.Column("created_at", DateTime, nullable=False),
        sa.Column("updated_at", DateTime, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"]),
        sa.ForeignKeyConstraint(["cooperative_id"], ["cooperatives.id"]),
    )
    op.create_index("ix_accounts_member", "personal_accounts", ["member_id"])
    op.create_index("ix_accounts_cooperative", "personal_accounts", ["cooperative_id"])
    op.create_index(
        "ix_accounts_cooperative_status", "personal_accounts", ["cooperative_id", "status"]
    )

    # PersonalAccountTransaction
    op.create_table(
        "personal_account_transactions",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), nullable=False),
        sa.Column("payment_id", UUID(as_uuid=True), nullable=True),
        sa.Column("distribution_id", UUID(as_uuid=True), nullable=True),
        sa.Column("transaction_number", String(50), nullable=False),
        sa.Column("transaction_date", DateTime, nullable=False),
        sa.Column("amount", Numeric(10, 2), nullable=False),
        sa.Column("type", String(50), nullable=False),
        sa.Column("description", String(500), nullable=True),
        sa.Column("created_at", DateTime, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["account_id"], ["personal_accounts.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
    )
    op.create_index("ix_transactions_account", "personal_account_transactions", ["account_id"])
    op.create_index(
        "ix_transactions_account_date",
        "personal_account_transactions",
        ["account_id", "transaction_date"],
    )
    op.create_index("ix_transactions_type", "personal_account_transactions", ["type"])

    # PaymentDistribution
    op.create_table(
        "payment_distributions",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("payment_id", UUID(as_uuid=True), nullable=False),
        sa.Column("financial_subject_id", UUID(as_uuid=True), nullable=False),
        sa.Column("distribution_number", String(50), nullable=False),
        sa.Column("distributed_at", DateTime, nullable=False),
        sa.Column("amount", Numeric(10, 2), nullable=False),
        sa.Column("priority", Integer, nullable=False),
        sa.Column("status", String(50), nullable=False, default="applied"),
        sa.Column("created_at", DateTime, nullable=False),
        sa.Column("updated_at", DateTime, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.ForeignKeyConstraint(["financial_subject_id"], ["financial_subjects.id"]),
    )
    op.create_index("ix_distributions_payment", "payment_distributions", ["payment_id"])
    op.create_index(
        "ix_distributions_financial_subject", "payment_distributions", ["financial_subject_id"]
    )
    op.create_index("ix_distributions_status", "payment_distributions", ["status"])

    # SettingsModule
    op.create_table(
        "settings_modules",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("cooperative_id", UUID(as_uuid=True), nullable=False),
        sa.Column("module_name", String(100), nullable=False),
        sa.Column("is_active", Boolean, nullable=False, default=True),
        sa.Column("created_at", DateTime, nullable=False),
        sa.Column("updated_at", DateTime, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["cooperative_id"], ["cooperatives.id"]),
    )
    op.create_index("ix_settings_modules_cooperative", "settings_modules", ["cooperative_id"])
    op.create_unique_constraint(
        "uq_settings_module_coop_name", "settings_modules", ["cooperative_id", "module_name"]
    )

    # PaymentDistributionRule
    op.create_table(
        "payment_distribution_rules",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("settings_module_id", UUID(as_uuid=True), nullable=False),
        sa.Column("rule_type", String(50), nullable=False),
        sa.Column("priority", Integer, nullable=False),
        sa.Column("contribution_type_id", UUID(as_uuid=True), nullable=True),
        sa.Column("meter_type", String(50), nullable=True),
        sa.Column("is_active", Boolean, nullable=False, default=True),
        sa.Column("created_at", DateTime, nullable=False),
        sa.Column("updated_at", DateTime, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["settings_module_id"], ["settings_modules.id"]),
        sa.ForeignKeyConstraint(["contribution_type_id"], ["contribution_types.id"]),
    )
    op.create_index(
        "ix_distribution_rules_module", "payment_distribution_rules", ["settings_module_id"]
    )
    op.create_index("ix_distribution_rules_type", "payment_distribution_rules", ["rule_type"])
    op.create_unique_constraint(
        "uq_distribution_rule_module_priority",
        "payment_distribution_rules",
        ["settings_module_id", "priority"],
    )

    # ContributionTypeSettings
    op.create_table(
        "contribution_type_settings",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("settings_module_id", UUID(as_uuid=True), nullable=False),
        sa.Column("contribution_type_id", UUID(as_uuid=True), nullable=False),
        sa.Column("default_amount", Numeric(10, 2), nullable=True),
        sa.Column("is_mandatory", Boolean, nullable=False, default=True),
        sa.Column("calculation_period", String(50), nullable=False, default="year"),
        sa.Column("created_at", DateTime, nullable=False),
        sa.Column("updated_at", DateTime, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["settings_module_id"], ["settings_modules.id"]),
        sa.ForeignKeyConstraint(["contribution_type_id"], ["contribution_types.id"]),
    )
    op.create_unique_constraint(
        "uq_contribution_type_settings_module_type",
        "contribution_type_settings",
        ["settings_module_id", "contribution_type_id"],
    )

    # MeterTariff
    op.create_table(
        "meter_tariffs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("settings_module_id", UUID(as_uuid=True), nullable=False),
        sa.Column("meter_type", String(50), nullable=False),
        sa.Column("tariff_per_unit", Numeric(10, 2), nullable=False),
        sa.Column("valid_from", DateTime, nullable=False),
        sa.Column("valid_to", DateTime, nullable=True),
        sa.Column("created_at", DateTime, nullable=False),
        sa.Column("updated_at", DateTime, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["settings_module_id"], ["settings_modules.id"]),
    )
    op.create_index("ix_meter_tariffs_module", "meter_tariffs", ["settings_module_id"])
    op.create_index("ix_meter_tariffs_type", "meter_tariffs", ["meter_type"])
    op.create_index("ix_meter_tariffs_valid_from", "meter_tariffs", ["valid_from"])


def downgrade() -> None:
    # Reverse order of creation
    op.drop_table("meter_tariffs")
    op.drop_table("contribution_type_settings")
    op.drop_table("payment_distribution_rules")
    op.drop_table("settings_modules")
    op.drop_table("payment_distributions")
    op.drop_table("personal_account_transactions")
    op.drop_table("personal_accounts")
    op.drop_table("member_plots")
    op.drop_table("members")
