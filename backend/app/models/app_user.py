"""AppUser model - re-export from Clean Architecture modules."""
from app.modules.administration.infrastructure.models import AppUserModel as AppUser

__all__ = ["AppUser"]
