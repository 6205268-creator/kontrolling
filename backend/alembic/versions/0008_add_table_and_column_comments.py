"""add table and column comments

Revision ID: 0008
Revises: 0007
Create Date: 2026-02-22

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Комментарии к таблицам
    op.execute(
        "COMMENT ON TABLE cooperatives IS 'Садоводческие товарищества (СТ) — основные организации в системе'"
    )
    op.execute(
        "COMMENT ON TABLE owners IS 'Владельцы — физические и юридические лица, владеющие участками и приборами учёта'"
    )
    op.execute("COMMENT ON TABLE land_plots IS 'Земельные участки в садоводческих товариществах'")
    op.execute(
        "COMMENT ON TABLE plot_ownerships IS 'Права собственности на земельные участки (периоды и доли)'"
    )
    op.execute(
        "COMMENT ON TABLE financial_subjects IS 'Финансовые субъекты — центры финансовой ответственности (участки, счётчики, решения)'"
    )
    op.execute(
        "COMMENT ON TABLE contribution_types IS 'Справочник видов взносов (членский, целевой, за услуги)'"
    )
    op.execute("COMMENT ON TABLE accruals IS 'Начисления по финансовым субъектам (взносы, услуги)'")
    op.execute(
        "COMMENT ON TABLE payments IS 'Платежи по финансовым субъектам (поступления от владельцев)'"
    )
    op.execute(
        "COMMENT ON TABLE expense_categories IS 'Справочник категорий расходов СТ (дороги, зарплата, материалы)'"
    )
    op.execute(
        "COMMENT ON TABLE expenses IS 'Расходы садоводческих товариществ (ремонт, зарплата, материалы)'"
    )
    op.execute("COMMENT ON TABLE meters IS 'Приборы учёта (счётчики воды и электроэнергии)'")
    op.execute(
        "COMMENT ON TABLE meter_readings IS 'Показания приборов учёта (вода, электроэнергия)'"
    )
    op.execute(
        "COMMENT ON TABLE app_users IS 'Пользователи системы (администраторы, председатели, казначеи)'"
    )

    # Комментарии к колонкам cooperatives
    op.execute("COMMENT ON COLUMN cooperatives.id IS 'Уникальный идентификатор СТ'")
    op.execute("COMMENT ON COLUMN cooperatives.name IS 'Название садоводческого товарищества'")
    op.execute(
        "COMMENT ON COLUMN cooperatives.unp IS 'УНП (учётный номер плательщика) — идентификационный код организации'"
    )
    op.execute("COMMENT ON COLUMN cooperatives.address IS 'Юридический адрес СТ'")
    op.execute("COMMENT ON COLUMN cooperatives.created_at IS 'Дата и время создания записи'")
    op.execute(
        "COMMENT ON COLUMN cooperatives.updated_at IS 'Дата и время последнего обновления записи'"
    )

    # Комментарии к колонкам owners
    op.execute("COMMENT ON COLUMN owners.id IS 'Уникальный идентификатор владельца'")
    op.execute(
        "COMMENT ON COLUMN owners.owner_type IS 'Тип владельца: physical (физ. лицо) или legal (юр. лицо)'"
    )
    op.execute("COMMENT ON COLUMN owners.name IS 'ФИО физического лица или название организации'")
    op.execute("COMMENT ON COLUMN owners.tax_id IS 'УНП (для юр. лиц) или ИНН (для физ. лиц)'")
    op.execute("COMMENT ON COLUMN owners.contact_phone IS 'Контактный телефон'")
    op.execute("COMMENT ON COLUMN owners.contact_email IS 'Контактный email'")
    op.execute("COMMENT ON COLUMN owners.created_at IS 'Дата и время создания записи'")
    op.execute("COMMENT ON COLUMN owners.updated_at IS 'Дата и время последнего обновления записи'")

    # Комментарии к колонкам land_plots
    op.execute("COMMENT ON COLUMN land_plots.id IS 'Уникальный идентификатор участка'")
    op.execute(
        "COMMENT ON COLUMN land_plots.cooperative_id IS 'ID СТ, которому принадлежит участок'"
    )
    op.execute("COMMENT ON COLUMN land_plots.plot_number IS 'Номер участка (внутренний в СТ)'")
    op.execute("COMMENT ON COLUMN land_plots.area_sqm IS 'Площадь участка в квадратных метрах'")
    op.execute(
        "COMMENT ON COLUMN land_plots.cadastral_number IS 'Кадастровый номер (государственный реестр)'"
    )
    op.execute(
        "COMMENT ON COLUMN land_plots.status IS 'Статус участка: active (активен), vacant (свободен), archived (архивирован)'"
    )
    op.execute("COMMENT ON COLUMN land_plots.created_at IS 'Дата и время создания записи'")
    op.execute(
        "COMMENT ON COLUMN land_plots.updated_at IS 'Дата и время последнего обновления записи'"
    )

    # Комментарии к колонкам plot_ownerships
    op.execute(
        "COMMENT ON COLUMN plot_ownerships.id IS 'Уникальный идентификатор записи о праве собственности'"
    )
    op.execute("COMMENT ON COLUMN plot_ownerships.land_plot_id IS 'ID земельного участка'")
    op.execute("COMMENT ON COLUMN plot_ownerships.owner_id IS 'ID владельца (физ. или юр. лицо)'")
    op.execute(
        "COMMENT ON COLUMN plot_ownerships.share_numerator IS 'Числитель доли (например, 1 для 1/2)'"
    )
    op.execute(
        "COMMENT ON COLUMN plot_ownerships.share_denominator IS 'Знаменатель доли (например, 2 для 1/2)'"
    )
    op.execute(
        "COMMENT ON COLUMN plot_ownerships.is_primary IS 'Основной владелец (член СТ). Только один на участок.'"
    )
    op.execute(
        "COMMENT ON COLUMN plot_ownerships.valid_from IS 'Дата начала права собственности (когда СТ узнало о переходе права)'"
    )
    op.execute(
        "COMMENT ON COLUMN plot_ownerships.valid_to IS 'Дата прекращения права собственности (NULL если текущее)'"
    )
    op.execute("COMMENT ON COLUMN plot_ownerships.created_at IS 'Дата и время создания записи'")
    op.execute(
        "COMMENT ON COLUMN plot_ownerships.updated_at IS 'Дата и время последнего обновления записи'"
    )

    # Комментарии к колонкам financial_subjects
    op.execute(
        "COMMENT ON COLUMN financial_subjects.id IS 'Уникальный идентификатор финансового субъекта'"
    )
    op.execute(
        "COMMENT ON COLUMN financial_subjects.subject_type IS 'Тип субъекта: LAND_PLOT, WATER_METER, ELECTRICITY_METER, GENERAL_DECISION'"
    )
    op.execute(
        "COMMENT ON COLUMN financial_subjects.subject_id IS 'ID бизнес-объекта (участок, счётчик и т.д.)'"
    )
    op.execute(
        "COMMENT ON COLUMN financial_subjects.cooperative_id IS 'ID СТ, которому принадлежит субъект'"
    )
    op.execute(
        "COMMENT ON COLUMN financial_subjects.code IS 'Уникальный код для платёжных документов'"
    )
    op.execute(
        "COMMENT ON COLUMN financial_subjects.status IS 'Статус: active (активен), closed (закрыт)'"
    )
    op.execute("COMMENT ON COLUMN financial_subjects.created_at IS 'Дата и время создания записи'")

    # Комментарии к колонкам contribution_types
    op.execute("COMMENT ON COLUMN contribution_types.id IS 'Уникальный идентификатор вида взноса'")
    op.execute(
        "COMMENT ON COLUMN contribution_types.name IS 'Название вида взноса (например, ''Членский взнос'')'"
    )
    op.execute(
        "COMMENT ON COLUMN contribution_types.code IS 'Уникальный код вида взноса (например, ''MEMBER'', ''TARGET'')'"
    )
    op.execute("COMMENT ON COLUMN contribution_types.description IS 'Описание вида взноса'")
    op.execute("COMMENT ON COLUMN contribution_types.created_at IS 'Дата и время создания записи'")

    # Комментарии к колонкам accruals
    op.execute("COMMENT ON COLUMN accruals.id IS 'Уникальный идентификатор начисления'")
    op.execute("COMMENT ON COLUMN accruals.financial_subject_id IS 'ID финансового субъекта'")
    op.execute(
        "COMMENT ON COLUMN accruals.contribution_type_id IS 'ID вида взноса (членский, целевой и т.д.)'"
    )
    op.execute("COMMENT ON COLUMN accruals.amount IS 'Сумма начисления в BYN'")
    op.execute("COMMENT ON COLUMN accruals.accrual_date IS 'Дата начисления'")
    op.execute(
        "COMMENT ON COLUMN accruals.period_start IS 'Начало периода, за который произведено начисление'"
    )
    op.execute("COMMENT ON COLUMN accruals.period_end IS 'Конец периода (опционально)'")
    op.execute(
        "COMMENT ON COLUMN accruals.status IS 'Статус: created (создано), applied (применено), cancelled (отменено)'"
    )
    op.execute("COMMENT ON COLUMN accruals.created_at IS 'Дата и время создания записи'")
    op.execute(
        "COMMENT ON COLUMN accruals.updated_at IS 'Дата и время последнего обновления записи'"
    )

    # Комментарии к колонкам payments
    op.execute("COMMENT ON COLUMN payments.id IS 'Уникальный идентификатор платежа'")
    op.execute("COMMENT ON COLUMN payments.financial_subject_id IS 'ID финансового субъекта'")
    op.execute("COMMENT ON COLUMN payments.payer_owner_id IS 'ID владельца, совершившего платёж'")
    op.execute("COMMENT ON COLUMN payments.amount IS 'Сумма платежа в BYN'")
    op.execute("COMMENT ON COLUMN payments.payment_date IS 'Дата совершения платежа'")
    op.execute(
        "COMMENT ON COLUMN payments.document_number IS 'Номер платёжного документа (квитанция, платёжка)'"
    )
    op.execute("COMMENT ON COLUMN payments.description IS 'Описание/назначение платежа'")
    op.execute(
        "COMMENT ON COLUMN payments.status IS 'Статус: confirmed (подтверждён), cancelled (отменён)'"
    )
    op.execute("COMMENT ON COLUMN payments.created_at IS 'Дата и время создания записи'")
    op.execute(
        "COMMENT ON COLUMN payments.updated_at IS 'Дата и время последнего обновления записи'"
    )

    # Комментарии к колонкам expense_categories
    op.execute(
        "COMMENT ON COLUMN expense_categories.id IS 'Уникальный идентификатор категории расхода'"
    )
    op.execute(
        "COMMENT ON COLUMN expense_categories.name IS 'Название категории (например, ''Дороги'', ''Зарплата'')'"
    )
    op.execute(
        "COMMENT ON COLUMN expense_categories.code IS 'Уникальный код категории (например, ''ROADS'', ''SALARY'')'"
    )
    op.execute("COMMENT ON COLUMN expense_categories.description IS 'Описание категории расхода'")
    op.execute("COMMENT ON COLUMN expense_categories.created_at IS 'Дата и время создания записи'")

    # Комментарии к колонкам expenses
    op.execute("COMMENT ON COLUMN expenses.id IS 'Уникальный идентификатор расхода'")
    op.execute("COMMENT ON COLUMN expenses.cooperative_id IS 'ID СТ, совершившего расход'")
    op.execute("COMMENT ON COLUMN expenses.category_id IS 'ID категории расхода'")
    op.execute("COMMENT ON COLUMN expenses.amount IS 'Сумма расхода в BYN'")
    op.execute("COMMENT ON COLUMN expenses.expense_date IS 'Дата совершения расхода'")
    op.execute(
        "COMMENT ON COLUMN expenses.document_number IS 'Номер платёжного документа (платёжное поручение, чек)'"
    )
    op.execute("COMMENT ON COLUMN expenses.description IS 'Описание расхода'")
    op.execute(
        "COMMENT ON COLUMN expenses.status IS 'Статус: created (создан), confirmed (подтверждён), cancelled (отменён)'"
    )
    op.execute("COMMENT ON COLUMN expenses.created_at IS 'Дата и время создания записи'")
    op.execute(
        "COMMENT ON COLUMN expenses.updated_at IS 'Дата и время последнего обновления записи'"
    )

    # Комментарии к колонкам meters
    op.execute("COMMENT ON COLUMN meters.id IS 'Уникальный идентификатор прибора учёта'")
    op.execute("COMMENT ON COLUMN meters.owner_id IS 'ID владельца прибора учёта'")
    op.execute(
        "COMMENT ON COLUMN meters.meter_type IS 'Тип прибора: WATER (вода), ELECTRICITY (электроэнергия)'"
    )
    op.execute("COMMENT ON COLUMN meters.serial_number IS 'Серийный номер прибора учёта'")
    op.execute("COMMENT ON COLUMN meters.installation_date IS 'Дата установки прибора учёта'")
    op.execute(
        "COMMENT ON COLUMN meters.status IS 'Статус: active (активен), inactive (не активен)'"
    )
    op.execute("COMMENT ON COLUMN meters.created_at IS 'Дата и время создания записи'")
    op.execute("COMMENT ON COLUMN meters.updated_at IS 'Дата и время последнего обновления записи'")

    # Комментарии к колонкам meter_readings
    op.execute("COMMENT ON COLUMN meter_readings.id IS 'Уникальный идентификатор показания'")
    op.execute("COMMENT ON COLUMN meter_readings.meter_id IS 'ID прибора учёта'")
    op.execute(
        "COMMENT ON COLUMN meter_readings.reading_value IS 'Значение показания (объём или расход)'"
    )
    op.execute("COMMENT ON COLUMN meter_readings.reading_date IS 'Дата снятия показания'")
    op.execute("COMMENT ON COLUMN meter_readings.created_at IS 'Дата и время создания записи'")

    # Комментарии к колонкам app_users
    op.execute("COMMENT ON COLUMN app_users.id IS 'Уникальный идентификатор пользователя'")
    op.execute("COMMENT ON COLUMN app_users.username IS 'Имя пользователя для входа в систему'")
    op.execute("COMMENT ON COLUMN app_users.email IS 'Email пользователя'")
    op.execute("COMMENT ON COLUMN app_users.hashed_password IS 'Хеш пароля (bcrypt)'")
    op.execute(
        "COMMENT ON COLUMN app_users.role IS 'Роль пользователя: admin, chairman, treasurer'"
    )
    op.execute(
        "COMMENT ON COLUMN app_users.cooperative_id IS 'ID СТ пользователя (NULL для admin)'"
    )
    op.execute(
        "COMMENT ON COLUMN app_users.is_active IS 'Активность пользователя (True = может войти)'"
    )
    op.execute("COMMENT ON COLUMN app_users.created_at IS 'Дата и время создания записи'")
    op.execute(
        "COMMENT ON COLUMN app_users.updated_at IS 'Дата и время последнего обновления записи'"
    )


def downgrade() -> None:
    # Удаляем все комментарии (downgrade)
    # Для таблиц
    op.execute("COMMENT ON TABLE cooperatives IS NULL")
    op.execute("COMMENT ON TABLE owners IS NULL")
    op.execute("COMMENT ON TABLE land_plots IS NULL")
    op.execute("COMMENT ON TABLE plot_ownerships IS NULL")
    op.execute("COMMENT ON TABLE financial_subjects IS NULL")
    op.execute("COMMENT ON TABLE contribution_types IS NULL")
    op.execute("COMMENT ON TABLE accruals IS NULL")
    op.execute("COMMENT ON TABLE payments IS NULL")
    op.execute("COMMENT ON TABLE expense_categories IS NULL")
    op.execute("COMMENT ON TABLE expenses IS NULL")
    op.execute("COMMENT ON TABLE meters IS NULL")
    op.execute("COMMENT ON TABLE meter_readings IS NULL")
    op.execute("COMMENT ON TABLE app_users IS NULL")
