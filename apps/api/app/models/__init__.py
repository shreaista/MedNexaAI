"""Import models so SQLAlchemy registers mappings when the package loads."""

from app.models import ai as ai_models  # noqa: F401
from app.models import billing as billing_models  # noqa: F401
from app.models import clinical as clinical_models  # noqa: F401
from app.models import core as core_models  # noqa: F401

__all__ = ["ai_models", "billing_models", "clinical_models", "core_models"]
