"""Architecture Linter — проверка архитектурных ограничений проекта.

Запуск из каталога backend:
    python -m app.scripts.architecture_linter

Exit code:
    0 — все проверки пройдены
    1 — обнаружены нарушения
"""

import sys
from pathlib import Path

# Базовый путь — всегда от каталога backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def check_api_no_infrastructure_imports():
    """Проверка: API layer не импортирует из infrastructure.

    Нарушение: api/routes.py или api/schemas.py импортирует из infrastructure
    """
    violations = []
    modules_path = BASE_DIR / "app" / "modules"

    for module_dir in modules_path.iterdir():
        if not module_dir.is_dir() or module_dir.name in ("shared", "__pycache__"):
            continue

        api_dir = module_dir / "api"
        if not api_dir.exists():
            continue

        # Ищем файлы API
        for api_file in api_dir.glob("*.py"):
            if api_file.name.startswith("_"):
                continue

            with open(api_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Проверяем импорты из infrastructure
            if "from .infrastructure" in content or "from ..infrastructure" in content:
                violations.append(f"{api_file.relative_to(BASE_DIR)}: imports from infrastructure")

            # Проверяем прямые импорты моделей infrastructure
            if "infrastructure.models" in content:
                violations.append(
                    f"{api_file.relative_to(BASE_DIR)}: imports infrastructure.models"
                )

    return violations


def check_financial_subject_usage():
    """Check: Accrual and Payment use FinancialSubject.

    Violation: Accrual or Payment has direct FK to LandPlot/Meter
    without FinancialSubject intermediary.
    """
    violations = []

    # Check Accrual model
    accruals_models = BASE_DIR / "app" / "modules" / "accruals" / "infrastructure" / "models.py"
    if accruals_models.exists():
        with open(accruals_models, "r", encoding="utf-8") as f:
            content = f.read()

        # Find Accrual class
        if "class Accrual" in content:
            # Check for financial_subject_id
            if "financial_subject_id" not in content:
                violations.append(
                    "accruals/infrastructure/models.py: Accrual missing financial_subject_id"
                )

            # Check for direct FK to land_plot_id (without financial_subject)
            if "land_plot_id = Column" in content and "financial_subject_id" not in content:
                violations.append(
                    "accruals/infrastructure/models.py: Accrual has direct FK to LandPlot"
                )

    # Check Payment model
    payments_models = BASE_DIR / "app" / "modules" / "payments" / "infrastructure" / "models.py"
    if payments_models.exists():
        with open(payments_models, "r", encoding="utf-8") as f:
            content = f.read()

        if "class Payment" in content:
            if "financial_subject_id" not in content:
                violations.append(
                    "payments/infrastructure/models.py: Payment missing financial_subject_id"
                )

    return violations


def check_models_registered():
    """Check: All ORM models are registered in register_models.py.

    A module is considered registered if register_models.py imports
    that module's infrastructure (e.g. from app.modules.accruals.infrastructure import models).
    """
    violations = []

    register_models_path = BASE_DIR / "app" / "db" / "register_models.py"
    if not register_models_path.exists():
        return ["app/db/register_models.py: file does not exist"]

    with open(register_models_path, "r", encoding="utf-8") as f:
        registered_content = f.read()

    # Require each module's infrastructure to be imported
    modules_path = BASE_DIR / "app" / "modules"
    for module_dir in modules_path.iterdir():
        if not module_dir.is_dir() or module_dir.name in ("shared", "__pycache__", "deps"):
            continue

        infra_models = module_dir / "infrastructure" / "models.py"
        if not infra_models.exists():
            continue

        # Module is registered if we have an import like app.modules.<name>.infrastructure
        module_import_marker = f"modules.{module_dir.name}.infrastructure"
        if module_import_marker not in registered_content:
            violations.append(
                f"db/register_models.py: module {module_dir.name} infrastructure not imported"
            )

    return violations


def check_domain_no_framework_imports():
    """Check: Domain layer does not import frameworks.

    Violation: domain/*.py imports fastapi, sqlalchemy, pydantic
    """
    violations = []
    forbidden = ["fastapi", "sqlalchemy", "pydantic"]

    modules_path = BASE_DIR / "app" / "modules"
    for module_dir in modules_path.iterdir():
        if not module_dir.is_dir():
            continue

        domain_dir = module_dir / "domain"
        if not domain_dir.exists():
            continue

        for py_file in domain_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            for lib in forbidden:
                if f"import {lib}" in content or f"from {lib}" in content:
                    violations.append(f"{py_file.relative_to(BASE_DIR)}: imports {lib}")

    return violations


def check_no_direct_owner_fk():
    """Check: LandPlot does not have direct FK to Owner.

    Violation: LandPlot has owner_id (should be via PlotOwnership)
    """
    violations = []

    land_models = BASE_DIR / "app" / "modules" / "land_management" / "infrastructure" / "models.py"
    if land_models.exists():
        with open(land_models, "r", encoding="utf-8") as f:
            content = f.read()

        # Find LandPlot class
        if "class LandPlot" in content:
            # Check for direct owner_id
            import re

            # Find owner_id in LandPlot context
            landplot_match = re.search(r"class LandPlot.*?(?=class |\Z)", content, re.DOTALL)
            if landplot_match:
                landplot_content = landplot_match.group(0)
                if "owner_id = Column" in landplot_content:
                    violations.append(
                        "land_management/infrastructure/models.py: "
                        "LandPlot has direct FK to Owner (should be via PlotOwnership)"
                    )

    return violations


def run_all_checks():
    """Запустить все проверки и вернуть список нарушений."""
    all_violations = []

    checks = [
        ("API -> Infrastructure", check_api_no_infrastructure_imports),
        ("FinancialSubject", check_financial_subject_usage),
        ("Models Registration", check_models_registered),
        ("Domain -> Frameworks", check_domain_no_framework_imports),
        ("LandPlot -> Owner FK", check_no_direct_owner_fk),
    ]

    print("=" * 60)
    print("ARCHITECTURE LINTER")
    print("=" * 60)

    for check_name, check_func in checks:
        violations = check_func()
        status = "FAIL" if violations else "PASS"
        print(f"\n{check_name}: {status}")

        if violations:
            for v in violations:
                print(f"   -> {v}")
            all_violations.extend(violations)

    print("\n" + "=" * 60)
    if all_violations:
        print(f"RESULT: {len(all_violations)} violations found")
        print("=" * 60)
        return False
    else:
        print("RESULT: All checks passed")
        print("=" * 60)
        return True


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
