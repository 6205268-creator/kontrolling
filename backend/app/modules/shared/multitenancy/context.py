"""Helpers for extracting cooperative_id from request context.

In multitenant application, all queries must be filtered by cooperative_id.
This helper extracts cooperative_id from the current user context.
"""

from typing import Any
from uuid import UUID


def get_cooperative_id_from_context(current_user: dict[str, Any]) -> UUID:
    """Extract cooperative_id from current user context.

    Args:
        current_user: Dictionary with user data from JWT token (from deps.get_current_user).

    Returns:
        UUID of the cooperative.

    Raises:
        ValueError: If cooperative_id is not present in context.
    """
    cooperative_id = current_user.get("cooperative_id")
    if cooperative_id is None:
        raise ValueError("cooperative_id not found in user context")
    return UUID(cooperative_id) if isinstance(cooperative_id, str) else cooperative_id
