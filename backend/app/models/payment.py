"""Payment model - re-export from Clean Architecture modules."""
from app.modules.payments.infrastructure.models import PaymentModel as Payment

__all__ = ["Payment"]
