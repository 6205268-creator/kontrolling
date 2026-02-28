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
    
    Note: Models are imported via routers in main.py, so this function
    is kept for documentation purposes only.
    """
    # Models are now imported via routers in main.py
    # No need to import them here to avoid duplicate registration
    pass
