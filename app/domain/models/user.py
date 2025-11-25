from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class User:
    """Core user entity representing an account inside the platform."""

    email: str
    phone_number: str
    external_provider: str
    external_id: str
    external_claims: dict[str, str] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
