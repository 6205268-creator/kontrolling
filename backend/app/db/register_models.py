"""Register all module models for Alembic migrations.

This module imports all SQLAlchemy models from modules to ensure
they are included in Base.metadata for migration generation.

Usage in alembic/env.py:
    from app.db.register_models import import_all_models
    import_all_models()
"""


def import_all_models() -> None:
    """Import all models from modules for Alembic.

    This function should be called before alembic autogenerate
    to ensure all module tables are discovered.
    """
    # Import all module models to register them with Base.metadata
    from app.modules.accruals.infrastructure import models as accruals_models  # noqa: F401
    from app.modules.administration.infrastructure import (
        models as administration_models,  # noqa: F401
    )
    from app.modules.cooperative_core.infrastructure import (
        models as cooperative_core_models,  # noqa: F401
    )
    from app.modules.expenses.infrastructure import models as expenses_models  # noqa: F401
    from app.modules.financial_core.infrastructure import (
        models as financial_core_models,  # noqa: F401
    )
    from app.modules.land_management.infrastructure import (
        models as land_management_models,  # noqa: F401
    )
    from app.modules.meters.infrastructure import models as meters_models  # noqa: F401
    from app.modules.payment_distribution.infrastructure import (
        models as payment_distribution_models,  # noqa: F401
    )
    from app.modules.payments.infrastructure import models as payments_models  # noqa: F401
