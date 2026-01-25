"""Create DB tables (via Alembic) and seed. Run from backend_snt_v2 root."""
from __future__ import annotations

import os
import sys

# Ensure we run from backend_snt_v2 root
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_root)
sys.path.insert(0, _root)
os.environ.setdefault("DATABASE_URL", "sqlite:///./snt_v2.db")

from alembic import command
from alembic.config import Config


def main() -> None:
    cfg = Config(os.path.join(_root, "alembic.ini"))
    command.upgrade(cfg, "head")
    print("Migrations: ok")

    from scripts.seed import main as seed_main
    seed_main()


if __name__ == "__main__":
    main()
