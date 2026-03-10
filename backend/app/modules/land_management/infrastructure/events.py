"""Event publishing for land_management module.

Publishes domain events after database commit.
"""


def setup_event_listeners() -> None:
    """Setup SQLAlchemy event listeners for publishing domain events.

    Events are published after commit to ensure data consistency.
    """
    # Event listeners will be set up as needed
    # For now, events are published directly in use cases
    pass
